# ADR-009: Local LLM Gateway

## Decision
AI Core talks to local models only through an OpenAI-compatible LLM Gateway adapter.
The default endpoint targets a model runtime on the stationary PC via `host.docker.internal`.

## Why
- no hard dependency on Ollama, llama.cpp, vLLM or LocalAI;
- model replacement does not affect business logic;
- external/cloud providers can be added later behind explicit policy;
- infrastructure facts are collected deterministically before being sent to the model.

## Safety boundary
`v0.1.3-alpha` is read-only. The model cannot execute shell commands or mutations.
It receives normalized tool context and produces an explanation only.
If the LLM runtime is unavailable, AI Core returns a deterministic health summary instead of failing the request.
