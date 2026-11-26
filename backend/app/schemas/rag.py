"""Pydantic schemas for RAG document ingestion, agent workflows, and MCP."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    """Metadata of an uploaded knowledge-base document."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    chunk_count: int
    size_bytes: int
    created_at: datetime


class RagQueryRequest(BaseModel):
    """Query the user's vector index for relevant context chunks."""

    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class RagChunk(BaseModel):
    """Retrieved text snippet and source metadata."""

    document_id: str
    filename: str
    content: str
    score: float


class AgentTaskRequest(BaseModel):
    """Request to run a lightweight multi-step reasoning workflow."""

    goal: str = Field(min_length=3, max_length=4000)
    model: str | None = None
    use_rag: bool = True


class AgentStep(BaseModel):
    """Single step executed by the agent workflow."""

    step: str
    output: str


class AgentTaskResponse(BaseModel):
    """Final synthesized answer and execution trace."""

    goal: str
    model: str
    steps: list[AgentStep]
    final_answer: str
    total_tokens: int
    response_time_ms: float


class McpRequest(BaseModel):
    """JSON-RPC 2.0 request for the built-in MCP server bridge."""

    jsonrpc: str = "2.0"
    id: str | int | None = 1
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
