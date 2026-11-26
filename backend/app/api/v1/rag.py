"""Optional RAG document ingestion, vector query, Agent workflow, and MCP routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.models import Document, User
from app.db.session import get_db
from app.schemas.rag import (
    AgentTaskRequest,
    AgentTaskResponse,
    DocumentRead,
    McpRequest,
    RagChunk,
    RagQueryRequest,
)
from app.services.agent_service import AgentService
from app.services.mcp_service import mcp_service
from app.services.rag_service import extract_text_from_bytes, rag_service

router = APIRouter(prefix="/rag", tags=["RAG, Agents & MCP"])

ALLOWED_EXTENSIONS = (".pdf", ".txt", ".md", ".csv", ".json")


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Document]:
    """List documents uploaded by the authenticated user."""
    stmt = (
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    """Upload a PDF or text document and index it for local RAG retrieval."""
    settings = get_settings()
    if not settings.rag_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RAG is disabled")

    filename = file.filename or "document.txt"
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    raw_bytes = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    text = extract_text_from_bytes(filename, file.content_type or "text/plain", raw_bytes)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text content found in uploaded file",
        )

    doc = Document(
        user_id=current_user.id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw_bytes),
    )
    db.add(doc)
    db.flush()

    doc.chunk_count = rag_service.index_document(
        user_id=current_user.id,
        document_id=doc.id,
        filename=filename,
        text=text,
    )
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete an uploaded document and remove its chunks from the vector store."""
    doc = db.get(Document, document_id)
    if doc is None or doc.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    rag_service.delete_document(doc.id)
    db.delete(doc)
    db.commit()


@router.post("/query", response_model=list[RagChunk])
def query_documents(
    payload: RagQueryRequest,
    current_user: User = Depends(get_current_user),
) -> list[RagChunk]:
    """Query the authenticated user's indexed knowledge base."""
    hits = rag_service.query(user_id=current_user.id, query_text=payload.query, top_k=payload.top_k)
    return [RagChunk(**hit) for hit in hits]


@router.post("/agent", response_model=AgentTaskResponse)
async def run_agent_workflow(
    payload: AgentTaskRequest,
    current_user: User = Depends(get_current_user),
) -> AgentTaskResponse:
    """Execute a lightweight Plan -> Retrieve -> Synthesize agent workflow."""
    settings = get_settings()
    model = payload.model or current_user.preferred_model or settings.default_model
    agent = AgentService()
    try:
        result = await agent.run_workflow(
            user_id=current_user.id,
            goal=payload.goal,
            model=model,
            use_rag=payload.use_rag,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent workflow failed: {exc}",
        ) from exc
    return AgentTaskResponse(**result)


@router.post("/mcp")
def mcp_endpoint(
    payload: McpRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Handle JSON-RPC 2.0 MCP requests for local tools and resources."""
    settings = get_settings()
    if not settings.mcp_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server is disabled")
    return mcp_service.handle_rpc(
        rpc_id=payload.id,
        method=payload.method,
        params=payload.params,
        user_id=current_user.id,
    )
