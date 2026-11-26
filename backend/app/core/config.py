"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for API, security, database, Ollama, and RAG."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Offline AI Platform"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # Security & JWT
    jwt_secret_key: str = Field(
        default="dev-only-insecure-key-change-in-production-min-32-chars",
        min_length=16,
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate limiting
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # Database
    database_url: str = "sqlite:///./offline_ai.db"

    # Ollama (optimized for 2 CPU / 4 GB RAM, no GPU)
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "tinyllama"
    available_models: str = "tinyllama,qwen2.5:0.5b"
    ollama_timeout_seconds: int = 120

    # Optional RAG / ChromaDB / MCP
    rag_enabled: bool = True
    chroma_persist_dir: str = "./data/chroma"
    max_upload_size_mb: int = 10
    mcp_enabled: bool = True

    @field_validator("cors_origins")
    @classmethod
    def _validate_cors(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_models(self) -> list[str]:
        return [m.strip() for m in self.available_models.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
