"""Unit tests for RAG document ingestion, MCP JSON-RPC, and Agent workflows."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.services.ollama_service import OllamaResult, OllamaService
from tests.conftest import register_and_login


def test_rag_upload_query_and_delete(client: TestClient) -> None:
    headers = register_and_login(client)

    upload_res = client.post(
        "/api/v1/rag/documents",
        headers=headers,
        files={
            "file": (
                "architecture.txt",
                b"Offline AI Platform runs TinyLlama and Qwen2.5 0.5B on 2 CPU and 4 GB RAM.",
                "text/plain",
            )
        },
    )
    assert upload_res.status_code == 201, upload_res.text
    doc_id = upload_res.json()["id"]
    assert upload_res.json()["chunk_count"] >= 1

    query_res = client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={"query": "TinyLlama 4 GB RAM", "top_k": 2},
    )
    assert query_res.status_code == 200
    hits = query_res.json()
    assert len(hits) >= 1
    assert "TinyLlama" in hits[0]["content"]

    del_res = client.delete(f"/api/v1/rag/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204


def test_mcp_and_agent_endpoints(client: TestClient, monkeypatch) -> None:
    headers = register_and_login(client)

    # MCP tools/list
    list_res = client.post(
        "/api/v1/rag/mcp",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert list_res.status_code == 200
    tools = list_res.json()["result"]["tools"]
    assert any(t["name"] == "calculate" for t in tools)

    # MCP safe calculation
    calc_res = client.post(
        "/api/v1/rag/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "calculate", "arguments": {"expression": "(10 + 5) * 2"}},
        },
    )
    assert calc_res.status_code == 200
    assert calc_res.json()["result"]["content"][0]["text"] == "30.0"

    # Agent workflow
    monkeypatch.setattr(
        OllamaService,
        "chat_complete",
        AsyncMock(
            return_value=OllamaResult(
                content="Step complete.",
                model="tinyllama",
                prompt_tokens=10,
                completion_tokens=4,
                total_tokens=14,
                response_time_ms=50.0,
            )
        ),
    )
    agent_res = client.post(
        "/api/v1/rag/agent",
        headers=headers,
        json={"goal": "Summarize resource requirements", "use_rag": False},
    )
    assert agent_res.status_code == 200
    assert agent_res.json()["total_tokens"] == 28
    assert len(agent_res.json()["steps"]) == 2
