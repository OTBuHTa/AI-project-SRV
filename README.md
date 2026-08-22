# AI-project SRV

Local-first AI infrastructure management platform.

## Current milestone
`v0.3.8-alpha` — Agent token rotation from the Web Control Center.

## Architecture principles
- AI Core runs on the workstation.
- NAS is storage/backup only.
- Agents initiate outbound connections.
- Mutating actions require policy evaluation and approval.
- Workspace isolation is a first-class requirement.
- AI tools expose typed capabilities, never an unrestricted root shell.

## Implemented
- FastAPI service foundation.
- PostgreSQL + Redis via Docker Compose.
- Health and readiness endpoints.
- Alembic migration baseline.
- User / Organization / Workspace / Membership models.
- Role-to-permission mapping.
- Bootstrap owner flow.
- JWT access tokens and rotating opaque refresh sessions.
- Workspace-scoped authorization dependency.
- Hash-chained audit log.
- Single-use agent enrollment tokens.
- Revocable opaque agent identity credentials.
- Resource + Agent inventory.
- Agent heartbeat and CPU/RAM/disk/uptime telemetry.
- Read-only Linux Agent package with allowlisted capabilities.

## Quick start
1. Copy `.env.example` to `.env` and replace `JWT_SECRET`.
2. Run `docker compose up --build -d`.
3. Run `docker compose --profile tools run --rm --build migration`.
4. Open `http://localhost:8000/docs`.
5. Call `POST /api/v1/auth/bootstrap` once to create the initial owner/workspace.
6. Set `BOOTSTRAP_ENABLED=false` after initialization before external exposure.

## Current vertical slice
User -> authentication -> workspace membership -> permission -> policy/audit -> agent/tool execution -> result -> audit.



## v0.1.2-alpha

Adds telemetry history, 90-second online/offline evaluation, optional read-only Docker inventory, workspace WebSocket telemetry events, and the first deterministic AI Core tool: `GET /api/v1/ai/tools/resource-health/{resource_id}`.

The Linux agent still cannot execute arbitrary shell commands. Docker discovery only runs the fixed read-only `docker ps -a` command and exposes normalized inventory.


## v0.1.3-alpha — Local LLM Gateway + AI Assistant

The API now supports a provider-neutral local OpenAI-compatible LLM endpoint and persistent AI conversations.

Configure `.env`:

```env
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=qwen2.5:7b
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=90
```

Compatible runtimes include Ollama (OpenAI compatibility), llama.cpp server, vLLM and LocalAI.

New endpoints:

```text
POST /api/v1/ai/chat
GET  /api/v1/ai/conversations
GET  /api/v1/ai/conversations/{conversation_id}/messages
```

When `resource_id` is provided to `/ai/chat`, AI Core injects deterministic read-only health context for that resource. If the local model is unavailable, a deterministic fallback response is returned and the conversation remains persisted.


## v0.1.4-alpha — ActionPlan + Policy Engine + Approval

First controlled mutation path:

`user -> ActionPlan -> Policy Engine -> explicit approval -> AgentTask -> allowlisted Linux Agent capability -> result -> AuditLog`

Enabled write capability: `docker.container.restart` (risk level 2, approval required). Unknown mutations are denied by default.

### API
- `POST /api/v1/action-plans`
- `GET /api/v1/action-plans`
- `POST /api/v1/action-plans/{id}/approve`
- `POST /api/v1/action-plans/{id}/reject`
- agent-only task lease/result endpoints under `/api/v1/agents/{agent_id}/tasks/...`


## v0.1.5-alpha — AI Action Proposal + Verification

AI Assistant can now create a policy-controlled proposal for the first mutation capability, `docker.container.restart`. Capability selection is deterministic and server-side; the LLM cannot invent executable commands.

Flow:

`AI proposal -> pending approval -> explicit user approval -> AgentTask -> execution -> verifying -> fresh heartbeat -> verified success/failure -> AuditLog`

New endpoint:

```text
POST /api/v1/ai/action-proposals
```

Verification is independent from command exit status. A successful restart is accepted only after fresh Docker inventory observes the target container in `running` state.
