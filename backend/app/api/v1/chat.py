"""Chat completion (streaming & non-streaming) and Ollama model discovery routes."""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.metrics import LLM_RESPONSE_DURATION_SECONDS, LLM_TOKENS_TOTAL
from app.db.models import Conversation, Message, User
from app.db.session import SessionLocal, get_db
from app.schemas.chat import ChatRequest, ChatResponse, MessageRead, ModelInfo
from app.services.ollama_service import OllamaService
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Chat & AI"])


def _build_prompt_messages(
    conv: Conversation, user_id: str, latest_prompt: str, use_rag: bool
) -> list[dict[str, str]]:
    """Build bounded chat context suitable for TinyLlama / Qwen2.5 0.5B."""
    messages: list[dict[str, str]] = []
    system_parts: list[str] = []

    if conv.system_prompt:
        system_parts.append(conv.system_prompt)
    else:
        system_parts.append("You are a helpful, concise offline AI assistant.")

    if use_rag:
        hits = rag_service.query(user_id=user_id, query_text=latest_prompt, top_k=3)
        if hits:
            context = "\n\n".join(f"[{h['filename']}] {h['content']}" for h in hits)
            system_parts.append(
                "Use the following local document excerpts when relevant:\n" + context
            )

    messages.append({"role": "system", "content": "\n\n".join(system_parts)})

    # Keep the most recent 10 turns to stay well within small-model context windows.
    for msg in conv.messages[-10:]:
        if msg.role in {"user", "assistant"}:
            messages.append({"role": msg.role, "content": msg.content})
    return messages


def _record_llm_metrics(
    model: str, prompt_tokens: int, completion_tokens: int, response_time_ms: float
) -> None:
    LLM_TOKENS_TOTAL.labels(model=model, token_type="prompt").inc(prompt_tokens)
    LLM_TOKENS_TOTAL.labels(model=model, token_type="completion").inc(completion_tokens)
    LLM_RESPONSE_DURATION_SECONDS.labels(model=model).observe(response_time_ms / 1000.0)


@router.get("/models", response_model=list[ModelInfo])
async def list_available_models(
    _: User = Depends(get_current_user),
) -> list[ModelInfo]:
    """Return available Ollama models installed locally."""
    service = OllamaService()
    models = await service.list_models()
    return [ModelInfo(**m) for m in models]


@router.post("", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message to Ollama (SSE streaming when `stream=true`, JSON otherwise)."""
    conv = db.get(Conversation, payload.conversation_id)
    if conv is None or conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    active_model = payload.model or conv.model
    use_rag = payload.use_rag if payload.use_rag is not None else conv.use_rag

    # Auto-title new conversations from the first prompt.
    if conv.title == "New Conversation" and not conv.messages:
        conv.title = payload.message.strip()[:60] or "New Conversation"
    if payload.model and payload.model != conv.model:
        conv.model = payload.model

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.message,
        model=active_model,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(conv)
    db.refresh(user_msg)

    prompt_messages = _build_prompt_messages(conv, current_user.id, payload.message, use_rag)
    ollama = OllamaService()

    if not payload.stream:
        try:
            result = await ollama.chat_complete(
                model=active_model,
                messages=prompt_messages,
                temperature=payload.temperature,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama inference failed: {exc}",
            ) from exc

        _record_llm_metrics(
            active_model,
            result.prompt_tokens,
            result.completion_tokens,
            result.response_time_ms,
        )
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=result.content,
            model=active_model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            response_time_ms=result.response_time_ms,
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return ChatResponse(
            conversation_id=conv.id,
            user_message=MessageRead.model_validate(user_msg),
            assistant_message=MessageRead.model_validate(assistant_msg),
        )

    conv_id = conv.id
    user_msg_id = user_msg.id

    async def event_generator() -> AsyncIterator[str]:
        yield f"data: {json.dumps({'type': 'start', 'user_message_id': user_msg_id})}\n\n"
        try:
            async for event in ollama.chat_stream(
                model=active_model,
                messages=prompt_messages,
                temperature=payload.temperature,
            ):
                if event["type"] == "token":
                    yield f"data: {json.dumps(event)}\n\n"
                elif event["type"] == "done":
                    _record_llm_metrics(
                        active_model,
                        event["prompt_tokens"],
                        event["completion_tokens"],
                        event["response_time_ms"],
                    )
                    with SessionLocal() as stream_db:
                        assistant_msg = Message(
                            conversation_id=conv_id,
                            role="assistant",
                            content=event["content"],
                            model=active_model,
                            prompt_tokens=event["prompt_tokens"],
                            completion_tokens=event["completion_tokens"],
                            total_tokens=event["total_tokens"],
                            response_time_ms=event["response_time_ms"],
                        )
                        stream_db.add(assistant_msg)
                        stream_db.commit()
                        stream_db.refresh(assistant_msg)
                        done_payload = {
                            "type": "done",
                            "assistant_message": MessageRead.model_validate(
                                assistant_msg
                            ).model_dump(mode="json"),
                        }
                    yield f"data: {json.dumps(done_payload)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
