from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()

class LLMUnavailable(RuntimeError):
    pass

class LLMGateway:
    """Provider-neutral gateway for local OpenAI-compatible LLM runtimes.

    Works with Ollama / llama.cpp / vLLM / LocalAI when their OpenAI-compatible
    /v1/chat/completions endpoint is enabled. No provider-specific logic leaks
    into AI Core.
    """

    async def chat(self, messages: list[dict], *, temperature: float = 0.2) -> tuple[str, str]:
        url = settings.llm_base_url.rstrip('/') + '/chat/completions'
        headers = {'Content-Type': 'application/json'}
        if settings.llm_api_key:
            headers['Authorization'] = f'Bearer {settings.llm_api_key}'
        payload = {
            'model': settings.llm_model,
            'messages': messages,
            'temperature': temperature,
            'stream': False,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            content = data['choices'][0]['message']['content']
            return str(content).strip(), str(data.get('model') or settings.llm_model)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMUnavailable(str(exc)) from exc

llm_gateway = LLMGateway()
