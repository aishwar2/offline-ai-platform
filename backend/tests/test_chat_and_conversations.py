"""Unit tests for conversations, chat completions, model switching, export, and health."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.services.ollama_service import OllamaResult, OllamaService
from tests.conftest import register_and_login


def test_health_and_metrics_endpoints(client: TestClient) -> None:
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "offline_ai_http_requests_total" in metrics.text


def test_conversation_crud_chat_and_export(client: TestClient, monkeypatch) -> None:
    headers = register_and_login(client)

    mock_result = OllamaResult(
        content="TinyLlama is a compact 1.1B parameter language model.",
        model="tinyllama",
        prompt_tokens=12,
        completion_tokens=10,
        total_tokens=22,
        response_time_ms=145.5,
    )
    monkeypatch.setattr(OllamaService, "chat_complete", AsyncMock(return_value=mock_result))

    # Create conversation
    conv_res = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "New Conversation", "model": "tinyllama"},
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # Non-streaming chat completion
    chat_res = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"conversation_id": conv_id, "message": "What is TinyLlama?", "stream": False},
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["assistant_message"]["total_tokens"] == 22
    assert data["assistant_message"]["response_time_ms"] == 145.5

    # Switch model on conversation
    patch_res = client.patch(
        f"/api/v1/conversations/{conv_id}",
        headers=headers,
        json={"model": "qwen2.5:0.5b"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["model"] == "qwen2.5:0.5b"

    # Export Markdown & JSON
    md_res = client.get(f"/api/v1/conversations/{conv_id}/export?format=markdown", headers=headers)
    assert md_res.status_code == 200
    assert "TinyLlama is a compact" in md_res.text

    json_res = client.get(f"/api/v1/conversations/{conv_id}/export?format=json", headers=headers)
    assert json_res.status_code == 200
    assert len(json_res.json()["messages"]) == 2

    # Delete conversation
    del_res = client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 204


def test_streaming_chat_sse(client: TestClient, monkeypatch) -> None:
    headers = register_and_login(client)
    conv_id = client.post("/api/v1/conversations", headers=headers, json={}).json()["id"]

    async def fake_stream(self, model, messages, temperature=0.7):
        yield {"type": "token", "content": "Hello "}
        yield {"type": "token", "content": "world!"}
        yield {
            "type": "done",
            "content": "Hello world!",
            "model": model,
            "prompt_tokens": 5,
            "completion_tokens": 2,
            "total_tokens": 7,
            "response_time_ms": 80.0,
        }

    monkeypatch.setattr(OllamaService, "chat_stream", fake_stream)
    res = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"conversation_id": conv_id, "message": "Say hi", "stream": True},
    )
    assert res.status_code == 200
    assert "Hello world!" in res.text
    assert '"total_tokens": 7' in res.text
