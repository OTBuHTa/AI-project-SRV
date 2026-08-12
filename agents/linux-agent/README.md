# AI-project SRV Linux Agent

Read-only alpha agent. It reports host identity and CPU/RAM/disk/uptime telemetry. It deliberately does **not** provide arbitrary shell execution.

## First enrollment
1. In the API create an enrollment token with `POST /api/v1/agents/enrollment-token` using an authenticated user, `X-Workspace-ID`, and a role with `agent.install`.
2. Install this package in a Python virtual environment.
3. Run:

```bash
AI_SRV_API_URL=https://your-ai-core.example \
AI_SRV_ENROLLMENT_TOKEN='enroll_...' \
ai-srv-agent --state-file /var/lib/ai-srv-agent/state.json --once
```

For development, omit `--once` to send heartbeats every 30 seconds.

The state file contains the agent credential and should be readable only by the service account.

## Reliability and secure state (v0.1.17-alpha)

Heartbeat, inventory submission, task polling, and task-result submission retry temporary transport failures, rate limits, and server errors with exponential backoff and jitter. After retries are exhausted, the daemon logs the failure, continues the remaining operations, and tries again during the next cycle instead of exiting.

Enrollment state is written atomically in the state file's directory, flushed to disk, and replaced only after the complete JSON document is durable. The agent restricts the state file to mode `0600` where the operating system supports POSIX permissions and validates required credentials when loading it.


## Controlled write capability (v0.1.4-alpha)

The only write capability is `docker.container.restart`. It is not callable directly by the LLM. The server must create an ActionPlan, Policy Engine assigns risk level 2, an authorized user must approve it, and the agent then executes the fixed `docker restart <validated-container>` argv form. No shell (`sh -c`) is used.
