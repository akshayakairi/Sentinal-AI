"""Tests for grounded incident reasoning."""

from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.schemas.reasoning import ReasoningRequest
from app.services.knowledge_base import InMemoryKnowledgeRetriever
from app.services.llm_client import GeneratedReasoning
from app.services.reasoning_service import IncidentReasoningService


@dataclass
class FakeIncident:
    id: str = "incident-1"
    endpoint_id: str = "endpoint-1"
    title: str = "Suspicious encoded PowerShell"
    summary: str = "Encoded PowerShell execution detected."
    severity: str = "high"


@dataclass
class FakeAlert:
    title: str = "Suspicious PowerShell Encoded Command"
    description: str = "Encoded command execution detected."
    mitre_technique: str | None = "T1059.001"


class FakeIncidentRepository:
    def get_by_id(self, incident_id: str):
        return FakeIncident() if incident_id == "incident-1" else None


class FakeAlertRepository:
    def list_by_incident(self, incident_id: str):
        return [FakeAlert()]


class FakeGenerator:
    def generate(self, incident, alerts, documents, question):
        return GeneratedReasoning(
            summary="AI summary",
            assessment="AI assessment grounded in supplied evidence.",
            recommended_actions=["Review script block logs."],
        )


def build_service(generator=None) -> IncidentReasoningService:
    return IncidentReasoningService(
        FakeIncidentRepository(),  # type: ignore[arg-type]
        FakeAlertRepository(),  # type: ignore[arg-type]
        InMemoryKnowledgeRetriever(),
        Settings(rag_top_k=2, llm_model="test-model" if generator else None),
        generator,
    )


def test_analyze_returns_grounded_powershell_guidance() -> None:
    result = build_service().analyze("incident-1", ReasoningRequest())

    assert result.incident_id == "incident-1"
    assert result.sources[0].id == "mitre-t1059-001"
    assert "T1059.001" in result.assessment
    assert result.disclaimer


def test_analyze_uses_configured_generator() -> None:
    result = build_service(FakeGenerator()).analyze("incident-1", ReasoningRequest())

    assert result.summary == "AI summary"
    assert result.model_used == "test-model"


def test_analyze_rejects_missing_incident() -> None:
    with pytest.raises(HTTPException) as exc_info:
        build_service().analyze("missing", ReasoningRequest())

    assert exc_info.value.status_code == 404
