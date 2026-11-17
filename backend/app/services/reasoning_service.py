"""Grounded incident reasoning service."""

import logging

from fastapi import HTTPException, status

from app.core.config import Settings
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.reasoning import IncidentReasoningResponse, ReasoningRequest, ReasoningSource
from app.services.knowledge_base import KnowledgeDocument, KnowledgeRetriever
from app.services.llm_client import ReasoningGenerator

logger = logging.getLogger(__name__)


class IncidentReasoningService:
    """Build transparent, retrieval-grounded investigation assistance."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        alert_repository: AlertRepository,
        knowledge_retriever: KnowledgeRetriever,
        settings: Settings,
        reasoning_generator: ReasoningGenerator | None = None,
    ) -> None:
        self._incident_repository = incident_repository
        self._alert_repository = alert_repository
        self._knowledge_retriever = knowledge_retriever
        self._settings = settings
        self._reasoning_generator = reasoning_generator

    def analyze(self, incident_id: str, request: ReasoningRequest) -> IncidentReasoningResponse:
        """Explain an incident from observed alerts and retrieved knowledge."""
        incident = self._incident_repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident was not found.")

        alerts = self._alert_repository.list_by_incident(incident_id)
        query = " ".join(filter(None, [incident.title, incident.summary, *[
            f"{alert.title} {alert.description} {alert.mitre_technique or ''}" for alert in alerts
        ], request.question]))
        documents = self._knowledge_retriever.retrieve(query, self._settings.rag_top_k)
        response = self._build_grounded_response(incident, alerts, documents)

        if self._reasoning_generator is None:
            return response
        try:
            generated = self._reasoning_generator.generate(incident, alerts, documents, request.question)
        except Exception:
            logger.exception("LLM reasoning failed for incident %s; returning grounded fallback.", incident_id)
            return response

        return response.model_copy(update={
            "summary": generated.summary,
            "assessment": generated.assessment,
            "recommended_actions": generated.recommended_actions,
            "model_used": self._settings.llm_model,
        })

    @staticmethod
    def _build_grounded_response(incident, alerts, documents: list[KnowledgeDocument]) -> IncidentReasoningResponse:
        techniques = sorted({alert.mitre_technique for alert in alerts if alert.mitre_technique})
        technique_text = f" ATT&CK techniques observed: {', '.join(techniques)}." if techniques else ""
        assessment = (
            f"The incident contains {len(alerts)} correlated alert(s) on endpoint {incident.endpoint_id}."
            f" Severity is {incident.severity}.{technique_text}"
        )
        actions = [
            "Validate the alert evidence, event chronology, and process or account context before containment.",
            "Preserve relevant logs and endpoint artifacts for the investigation record.",
        ]
        actions.extend(f"Review guidance for {document.title}." for document in documents)
        return IncidentReasoningResponse(
            incident_id=incident.id,
            summary=incident.summary,
            assessment=assessment,
            recommended_actions=actions,
            sources=[ReasoningSource(id=document.id, title=document.title, source_url=document.source_url) for document in documents],
        )
