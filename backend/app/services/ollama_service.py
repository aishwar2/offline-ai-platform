"""Async client wrapper for local Ollama LLM inference and model discovery."""

import json
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OllamaResult:
    """Normalized completion result with token counts and latency."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time_ms: float


class OllamaService:
    """Communicate with the local Ollama REST API over HTTP."""

    def __init__(self, base_url: str | None = None, timeout_seconds: int | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout_seconds or settings.ollama_timeout_seconds

    async def is_healthy(self) -> bool:
        """Check whether the Ollama daemon is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """List installed Ollama models, falling back to configured defaults if unreachable."""
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                if models:
                    return [
                        {
                            "name": item.get("name", ""),
                            "size_bytes": int(item.get("size", 0)),
                            "is_default": item.get("name", "").startswith(settings.default_model),
                        }
                        for item in models
                    ]
        except httpx.HTTPError as exc:
            logger.warning("Ollama /api/tags unavailable, using configured defaults: %s", exc)

        return [
            {
                "name": name,
                "size_bytes": 0,
                "is_default": name == settings.default_model,
            }
            for name in settings.allowed_models
        ]

    async def chat_complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> OllamaResult:
        """Execute a non-streaming Ollama chat completion."""
        start = time.perf_counter()
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        content = data.get("message", {}).get("content", "")
        prompt_tokens = int(data.get("prompt_eval_count") or _estimate_tokens(messages))
        completion_tokens = int(data.get("eval_count") or _estimate_text_tokens(content))
        return OllamaResult(
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            response_time_ms=round(elapsed_ms, 2),
        )

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream token chunks from Ollama's /api/chat NDJSON stream."""
        start = time.perf_counter()
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        accumulated: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        accumulated.append(token)
                        yield {"type": "token", "content": token}

                    if chunk.get("done"):
                        full_text = "".join(accumulated)
                        prompt_tokens = int(
                            chunk.get("prompt_eval_count") or _estimate_tokens(messages)
                        )
                        completion_tokens = int(
                            chunk.get("eval_count") or _estimate_text_tokens(full_text)
                        )
                        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
                        yield {
                            "type": "done",
                            "content": full_text,
                            "model": model,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                            "response_time_ms": elapsed_ms,
                        }


def _estimate_text_tokens(text: str) -> int:
    return max(1, len(text.split())) if text.strip() else 0


def _estimate_tokens(messages: list[dict[str, str]]) -> int:
    return sum(_estimate_text_tokens(msg.get("content", "")) for msg in messages)
