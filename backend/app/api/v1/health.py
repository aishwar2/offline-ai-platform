"""Kubernetes and Docker health, liveness, and readiness probes."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ollama_service import OllamaService

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def liveness() -> dict[str, str]:
    """Liveness probe confirming the API process is responsive."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)) -> JSONResponse:
    """Readiness probe validating database connectivity and Ollama reachability."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    ollama_ok = await OllamaService().is_healthy()
    code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=code,
        content={
            "status": "ready" if db_ok else "degraded",
            "database": "up" if db_ok else "down",
            "ollama": "up" if ollama_ok else "unreachable",
        },
    )


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> JSONResponse:
    """Combined health endpoint used by Docker Compose and CI smoke checks."""
    return await readiness(db)
