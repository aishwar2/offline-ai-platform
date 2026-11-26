"""Conversation CRUD and chat history export endpoints."""

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.metrics import ACTIVE_CONVERSATIONS
from app.db.models import Conversation, User
from app.db.session import get_db
from app.schemas.chat import (
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    ConversationUpdate,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def _get_owned_conversation(db: Session, conversation_id: str, user_id: str) -> Conversation:
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


def _sync_conversation_gauge(db: Session) -> None:
    count = db.scalar(select(func.count(Conversation.id))) or 0
    ACTIVE_CONVERSATIONS.set(count)


@router.get("", response_model=list[ConversationRead])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Conversation]:
    """List conversations belonging to the authenticated user."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Create a new chat conversation."""
    settings = get_settings()
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title,
        model=payload.model or current_user.preferred_model or settings.default_model,
        system_prompt=payload.system_prompt,
        use_rag=payload.use_rag,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    _sync_conversation_gauge(db)
    return conv


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Fetch a conversation with its ordered message history."""
    return _get_owned_conversation(db, conversation_id, current_user.id)


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Rename a conversation, switch its model, or toggle RAG."""
    conv = _get_owned_conversation(db, conversation_id, current_user.id)
    if payload.title is not None:
        conv.title = payload.title
    if payload.model is not None:
        conv.model = payload.model
    if payload.system_prompt is not None:
        conv.system_prompt = payload.system_prompt
    if payload.use_rag is not None:
        conv.use_rag = payload.use_rag

    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a conversation and all its messages."""
    conv = _get_owned_conversation(db, conversation_id, current_user.id)
    db.delete(conv)
    db.commit()
    _sync_conversation_gauge(db)


@router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    export_format: Literal["json", "markdown"] = Query(default="markdown", alias="format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export a conversation history as downloadable JSON or Markdown."""
    conv = _get_owned_conversation(db, conversation_id, current_user.id)

    if export_format == "json":
        payload = {
            "id": conv.id,
            "title": conv.title,
            "model": conv.model,
            "created_at": conv.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "model": msg.model,
                    "prompt_tokens": msg.prompt_tokens,
                    "completion_tokens": msg.completion_tokens,
                    "total_tokens": msg.total_tokens,
                    "response_time_ms": msg.response_time_ms,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in conv.messages
            ],
        }
        return Response(
            content=json.dumps(payload, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="conversation-{conv.id}.json"'
            },
        )

    lines = [
        f"# {conv.title}",
        "",
        f"- **Model:** `{conv.model}`",
        f"- **Exported:** {conv.updated_at.isoformat()}",
        "",
        "---",
        "",
    ]
    for msg in conv.messages:
        speaker = "User" if msg.role == "user" else msg.role.title()
        lines.append(f"### {speaker}")
        lines.append("")
        lines.append(msg.content)
        if msg.role == "assistant":
            lines.append("")
            lines.append(
                f"_Tokens: {msg.total_tokens} | Latency: {msg.response_time_ms:.1f} ms_"
            )
        lines.append("")

    return Response(
        content="\n".join(lines),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="conversation-{conv.id}.md"'
        },
    )
