# ADR-008: Telemetry first, LLM second

Status: accepted.

AI Core must consume normalized, auditable infrastructure facts before an LLM explains them. Heartbeats persist time-series samples; read-only health tools calculate deterministic findings from thresholds. LLM integration will call these tools rather than infer host state from conversation text.

Realtime delivery uses WebSocket for the MVP. A distributed event bus can replace the in-process hub when AI Core becomes multi-node.
