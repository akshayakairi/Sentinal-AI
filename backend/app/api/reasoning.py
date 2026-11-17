"""AI-assisted incident reasoning routes."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.reasoning import IncidentReasoningResponse, ReasoningRequest
from app.services.knowledge_base import InMemoryKnowledgeRetriever, KnowledgeRetriever, MITRE_DOCUMENTS
from app.services.llm_client import OpenAICompatibleReasoningGenerator
from app.services.reasoning_service import IncidentReasoningService
from app.services.vector_store import ChromaKnowledgeRetriever

router = APIRouter(prefix="/incidents", tags=["reasoning"])


def get_knowledge_retriever(settings: Settings) -> KnowledgeRetriever:
    """Select the configured retrieval implementation once per configuration."""
    return _build_knowledge_retriever(
        settings.rag_retriever,
        settings.chroma_persist_directory,
        settings.embedding_model_name,
    )


@lru_cache
def _build_knowledge_retriever(
    retriever_name: str,
    persist_directory: str,
    embedding_model_name: str,
) -> KnowledgeRetriever:
    """Cache expensive vector-store initialization using immutable settings."""
    if retriever_name == "chroma":
        return ChromaKnowledgeRetriever(MITRE_DOCUMENTS, persist_directory, embedding_model_name)
    return InMemoryKnowledgeRetriever()


def get_reasoning_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IncidentReasoningService:
    """Build the reasoning service for the current request."""
    generator = None
    if settings.llm_base_url and settings.llm_api_key and settings.llm_model:
        generator = OpenAICompatibleReasoningGenerator(settings)
    return IncidentReasoningService(
        IncidentRepository(db),
        AlertRepository(db),
        get_knowledge_retriever(settings),
        settings,
        generator,
    )


@router.post("/{incident_id}/reasoning", response_model=IncidentReasoningResponse)
async def analyze_incident(
    incident_id: str,
    payload: ReasoningRequest,
    reasoning_service: Annotated[IncidentReasoningService, Depends(get_reasoning_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> IncidentReasoningResponse:
    """Provide retrieval-grounded investigation assistance for an incident."""
    return reasoning_service.analyze(incident_id, payload)


