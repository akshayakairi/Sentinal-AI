"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    app_name: str = Field(default="SentinelAI API")
    app_version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    debug: bool = Field(default=False)

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/sentinelai"
    )

    jwt_secret_key: str = Field(default="change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    password_bcrypt_rounds: int = Field(default=12)

    rag_top_k: int = Field(default=3, ge=1, le=10)
    rag_retriever: Literal["memory", "chroma"] = Field(default="memory")
    chroma_persist_directory: str = Field(default=".sentinelai/chroma")
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2")
    llm_base_url: str | None = Field(default=None)
    llm_api_key: str | None = Field(default=None)
    llm_model: str | None = Field(default=None)
    llm_timeout_seconds: float = Field(default=20.0, gt=0, le=120)

    nvd_cve_api_url: str = Field(default="https://services.nvd.nist.gov/rest/json/cves/2.0")
    nvd_api_key: str | None = Field(default=None)
    threat_intelligence_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    cors_allow_origins: str = Field(default="http://localhost:5173")

    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
