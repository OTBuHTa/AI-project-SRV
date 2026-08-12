import argparse
import json
import logging
import os
import platform
import socket
import time
import subprocess
from pathlib import Path

import httpx
import psutil

from ai_srv_agent import __version__
from ai_srv_agent.credentials import (
    rotate_agent_token,
    token_needs_rotation,
)
from ai_srv_agent.reliability import retry_http
from ai_srv_agent.state import load_state, save_state

LOGGER = logging.getLogger("ai_srv_agent")

CAPABILITIES = [
    "system.metrics.read",
    "system.identity.read",
    "docker.inventory.read",
    "docker.container.restart",
]


def collect_metrics() -> dict:
    root = "/"
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(root)
    load_1m = None
    try:
        load_1m = os.getloadavg()[0]
    except (AttributeError, OSError):
        pass
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "disk_free_bytes": disk.free,
        "uptime_seconds": max(0, int(time.time() - psutil.boot_time())),
        "load_1m": load_1m,
    }



def collect_docker() -> dict:
    try:
        proc = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"available": False, "containers_total": 0, "containers_running": 0, "containers_stopped": 0, "containers": []}
    if proc.returncode != 0:
        return {"available": False, "containers_total": 0, "containers_running": 0, "containers_stopped": 0, "containers": []}
    containers=[]
    for line in proc.stdout.splitlines():
        try:
            item=json.loads(line)
            containers.append({"id":item.get("ID"),"name":item.get("Names"),"image":item.get("Image"),"status":item.get("Status"),"state":item.get("State")})
        except json.JSONDecodeError:
            continue
    running=sum(1 for c in containers if c.get("state")=="running")
    return {"available":True,"containers_total":len(containers),"containers_running":running,"containers_stopped":len(containers)-running,"containers":containers[:256]}



def collect_inventory() -> list[dict]:
    items = []

    cpu_freq = psutil.cpu_freq()
    items.append({
        "kind": "cpu",
        "external_id": "cpu",
        "name": platform.processor() or "CPU",
        "status": "online",
        "attributes": {
            "logical_cores": psutil.cpu_count(logical=True) or 0,
            "physical_cores": psutil.cpu_count(logical=False) or 0,
            "frequency_mhz": (
                cpu_freq.current if cpu_freq is not None else None
            ),
            "architecture": platform.machine(),
        },
    })

    memory = psutil.virtual_memory()
    items.append({
        "kind": "memory",
        "external_id": "memory",
        "name": "System memory",
        "status": "online",
        "attributes": {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
        },
    })

    seen_mountpoints = set()

    for partition in psutil.disk_partitions(all=False):
        mountpoint = partition.mountpoint

        if not mountpoint or mountpoint in seen_mountpoints:
            continue

        seen_mountpoints.add(mountpoint)

        try:
            usage = psutil.disk_usage(mountpoint)
        except (OSError, PermissionError):
            continue

        items.append({
            "kind": "filesystem",
            "external_id": mountpoint,
            "name": mountpoint,
            "status": "online",
            "attributes": {
                "device": partition.device,
                "fstype": partition.fstype,
                "options": partition.opts,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": usage.percent,
            },
        })

    addresses_by_interface = psutil.net_if_addrs()
    stats_by_interface = psutil.net_if_stats()

    for name in sorted(addresses_by_interface):
        addresses = []

        for address in addresses_by_interface[name]:
            addresses.append({
                "family": str(address.family),
                "address": address.address,
                "netmask": address.netmask,
                "broadcast": address.broadcast,
            })

        stats = stats_by_interface.get(name)
        is_up = stats.isup if stats is not None else False

        items.append({
            "kind": "network_interface",
            "external_id": name,
            "name": name,
            "status": "online" if is_up else "offline",
            "attributes": {
                "is_up": is_up,
                "speed_mbps": stats.speed if stats is not None else 0,
                "mtu": stats.mtu if stats is not None else None,
                "addresses": addresses,
            },
        })

    docker = collect_docker()

    if docker.get("available"):
        items.append({
            "kind": "docker_engine",
            "external_id": "docker",
            "name": "Docker",
            "status": "online",
            "attributes": {
                "containers_total": docker.get("containers_total", 0),
                "containers_running": docker.get("containers_running", 0),
                "containers_stopped": docker.get("containers_stopped", 0),
            },
        })

        for container in docker.get("containers", []):
            external_id = container.get("name") or container.get("id")

            if not external_id:
                continue

            state = container.get("state")

            items.append({
                "kind": "docker_container",
                "external_id": str(external_id),
                "name": container.get("name") or str(external_id),
                "status": "online" if state == "running" else "offline",
                "attributes": {
                    "container_id": container.get("id"),
                    "image": container.get("image"),
                    "state": state,
                    "status_text": container.get("status"),
                },
            })

    return items


def submit_inventory(state: dict) -> None:
    headers = {
        "Authorization": f"Bearer {state['agent_token']}",
    }

    payload = {"items": collect_inventory()}

    def request() -> None:
        response = httpx.post(
            (
                f"{state['api_url']}/api/v1/agents/"
                f"{state['agent_id']}/inventory"
            ),
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

    retry_http(request)



def enroll(api_url: str, enrollment_token: str, state_file: Path) -> dict:
    payload = {
        "enrollment_token": enrollment_token,
        "hostname": socket.gethostname(),
        "agent_version": __version__,
        "os_name": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "capabilities": CAPABILITIES,
    }
    def request() -> httpx.Response:
        response = httpx.post(
            f"{api_url}/api/v1/agents/enroll",
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response

    state = retry_http(request).json()
    state["api_url"] = api_url
    save_state(state_file, state)
    return state


def heartbeat(state: dict) -> None:
    payload = {
        "status": "healthy",
        "agent_version": __version__,
        "capabilities": CAPABILITIES,
        "metrics": collect_metrics(),
        "docker": collect_docker(),
    }
    headers = {"Authorization": f"Bearer {state['agent_token']}"}
    def request() -> None:
        response = httpx.post(
            f"{state['api_url']}/api/v1/agents/{state['agent_id']}/heartbeat",
            json=payload,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()

    retry_http(request)



def execute_task(task: dict) -> dict:
    started = time.monotonic()
    capability = task.get("capability")
    params = task.get("parameters") or {}
    if capability != "docker.container.restart":
        return {"status":"failed","exit_code":None,"stdout":"","stderr":"capability_not_allowed","duration_ms":int((time.monotonic()-started)*1000)}
    container = str(params.get("container", ""))
    import re
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", container):
        return {"status":"failed","exit_code":None,"stdout":"","stderr":"invalid_container_name","duration_ms":int((time.monotonic()-started)*1000)}
    try:
        inspect = subprocess.run(["docker","inspect","--format","{{.Name}}",container], capture_output=True, text=True, timeout=5, check=False)
        if inspect.returncode != 0:
            return {"status":"failed","exit_code":inspect.returncode,"stdout":"","stderr":"container_not_found","duration_ms":int((time.monotonic()-started)*1000)}
        proc = subprocess.run(["docker","restart",container], capture_output=True, text=True, timeout=30, check=False)
        return {"status":"success" if proc.returncode == 0 else "failed", "exit_code":proc.returncode, "stdout":proc.stdout[-12000:], "stderr":proc.stderr[-12000:], "duration_ms":int((time.monotonic()-started)*1000)}
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"status":"failed","exit_code":None,"stdout":"","stderr":type(exc).__name__,"duration_ms":int((time.monotonic()-started)*1000)}


def poll_and_execute_task(state: dict) -> None:
    headers = {"Authorization": f"Bearer {state['agent_token']}"}

    def poll() -> httpx.Response:
        response = httpx.get(
            f"{state['api_url']}/api/v1/agents/{state['agent_id']}/tasks/next",
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response

    task = retry_http(poll).json()
    if not task:
        return
    result = execute_task(task)

    def submit_result() -> None:
        response = httpx.post(
            f"{state['api_url']}/api/v1/agents/{state['agent_id']}/tasks/{task['task_id']}/result",
            json=result,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()

    retry_http(submit_result)


def run_cycle(
    state: dict,
    state_file: Path,
) -> None:
    if token_needs_rotation(state):
        try:
            rotate_agent_token(
                state,
                state_file,
            )
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            LOGGER.warning(
                "token rotation failed; "
                "agent will retry next cycle: %s",
                exc,
            )

    operations = (
        ("heartbeat", heartbeat),
        ("inventory", submit_inventory),
        ("task polling", poll_and_execute_task),
    )

    for name, operation in operations:
        try:
            operation(state)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            LOGGER.warning(
                "%s failed; agent will retry next cycle: %s",
                name,
                exc,
            )


def main() -> None:
    logging.basicConfig(
        level=os.getenv("AI_SRV_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="AI-project SRV read-only Linux agent")
    parser.add_argument("--api-url", default=os.getenv("AI_SRV_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--enrollment-token", default=os.getenv("AI_SRV_ENROLLMENT_TOKEN"))
    parser.add_argument("--state-file", default=os.getenv("AI_SRV_AGENT_STATE", "./agent-state.json"))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    state_file = Path(args.state_file)
    if state_file.exists():
        state = load_state(state_file)
    elif args.enrollment_token:
        state = enroll(args.api_url.rstrip("/"), args.enrollment_token, state_file)
    else:
        raise SystemExit("Enrollment token required for first start")

    while True:
        run_cycle(
            state,
            state_file,
        )
        if args.once:
            return
        time.sleep(int(state.get("heartbeat_interval_seconds", 30)))


if __name__ == "__main__":
    main()
