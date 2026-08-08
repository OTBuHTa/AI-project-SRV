from datetime import UTC, datetime, timedelta

def evaluate_resource(agent, resource) -> dict:
    metrics = agent.last_metrics or {}
    score = 100
    findings=[]
    if not agent.last_seen_at or datetime.now(UTC) - agent.last_seen_at > timedelta(seconds=90):
        return {"status":"offline","health_score":0,"severity":"critical","findings":["Agent heartbeat is stale or missing."]}
    cpu=float(metrics.get("cpu_percent",0))
    memory=float(metrics.get("memory_percent",0))
    disk=float(metrics.get("disk_percent",0))
    if cpu >= 90:
        score -= 30; findings.append("CPU utilization is critically high.")
    elif cpu >= 75:
        score -= 15; findings.append("CPU utilization is elevated.")
    if memory >= 90:
        score -= 30; findings.append("Memory utilization is critically high.")
    elif memory >= 80:
        score -= 15; findings.append("Memory utilization is elevated.")
    if disk >= 95:
        score -= 40; findings.append("Disk utilization is critically high.")
    elif disk >= 85:
        score -= 20; findings.append("Disk utilization is elevated.")
    if not findings:
        findings.append("No threshold violations detected in current host metrics.")
    severity = "healthy" if score >= 85 else "warning" if score >= 60 else "critical"
    return {"status":resource.status,"health_score":max(score,0),"severity":severity,"findings":findings}
