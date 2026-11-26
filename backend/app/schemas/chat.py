"""Pydantic schemas for conversations, messages, chat completion, and models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    """Payload to create a new conversation."""

    title: str = Field(default="New Conversation", min_length=1, max_length=200)
    model: str | None = Field(default=None, max_length=64)
    system_prompt: str | None = Field(default=None, max_length=4000)
    use_rag: bool = False


class ConversationUpdate(BaseModel):
    """Payload to update conversation metadata or switch model."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    model: str | None = Field(default=None, min_length=1, max_length=64)
    system_prompt: str | None = Field(default=None, max_length=4000)
    use_rag: bool | None = None


class MessageRead(BaseModel):
    """Serialized chat message including token and latency telemetry."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: Literal["system", "user", "assistant"]
    content: str
    model: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time_ms: float
    created_at: datetime


class ConversationRead(BaseModel):
    """Conversation summary without embedded message history."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    model: str
    system_prompt: str | None
    use_rag: bool
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationRead):
    """Conversation with full ordered message history."""

    messages: list[MessageRead] = []


class ChatRequest(BaseModel):
    """Request to send a user prompt to a conversation."""

    conversation_id: str
    message: str = Field(min_length=1, max_length=16000)
    model: str | None = Field(default=None, max_length=64)
    stream: bool = True
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    use_rag: bool | None = None


class ChatResponse(BaseModel):
    """Non-streaming chat response containing both user and assistant messages."""

    conversation_id: str
    user_message: MessageRead
    assistant_message: MessageRead


class ModelInfo(BaseModel):
    """Local Ollama model metadata."""

    name: str
    size_bytes: int = 0
    is_default: bool = False
