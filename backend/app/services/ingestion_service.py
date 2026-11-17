"""Endpoint event ingestion service."""

from datetime import timezone

from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.raw_event_repository import RawEventRepository
from app.schemas.detection import DetectionResult
from app.schemas.ingestion import (
    EndpointResponse,
    EventIngestionRequest,
    EventIngestionResponse,
)
from app.services.detection_service import DetectionService

SEVERITY_MAP = {
    "informational": "low",
    "info": "low",
    "low": "low",
    "medium": "medium",
    "moderate": "medium",
    "warning": "medium",
    "high": "high",
    "critical": "critical",
    "severe": "critical",
}

CATEGORY_MAP = {
    "process": "process_activity",
    "process_creation": "process_activity",
    "powershell": "script_execution",
    "script": "script_execution",
    "network": "network_activity",
    "dns": "network_activity",
    "authentication": "authentication",
    "logon": "authentication",
    "file": "file_activity",
    "registry": "registry_activity",
}


class IngestionService:
    """Service coordinating endpoint registration, event storage, and detection."""

    def __init__(
        self,
        endpoint_repository: EndpointRepository,
        raw_event_repository: RawEventRepository,
        detection_service: DetectionService | None = None,
    ) -> None:
        self._endpoint_repository = endpoint_repository
        self._raw_event_repository = raw_event_repository
        self._detection_service = detection_service

    def ingest_event(self, payload: EventIngestionRequest) -> EventIngestionResponse:
        """Register the endpoint if needed, normalize the event, store it, and evaluate detections."""
        occurred_at = payload.occurred_at.astimezone(timezone.utc)
        endpoint = self._endpoint_repository.get_by_hostname(payload.endpoint.hostname)
        if endpoint is None:
            endpoint = self._endpoint_repository.create(
                hostname=payload.endpoint.hostname,
                operating_system=payload.endpoint.operating_system,
                agent_version=payload.endpoint.agent_version,
                last_seen_at=occurred_at,
            )
        else:
            endpoint = self._endpoint_repository.update_last_seen(
                endpoint,
                operating_system=payload.endpoint.operating_system,
                agent_version=payload.endpoint.agent_version,
                last_seen_at=occurred_at,
            )

        normalized_severity = self.normalize_severity(payload.severity)
        event_category = self.categorize_event(payload.event_type, payload.source)
        normalized_summary = self.build_summary(
            hostname=endpoint.hostname,
            event_name=payload.event_name,
            source=payload.source,
            severity=normalized_severity,
            event_category=event_category,
        )

        event = self._raw_event_repository.create(
            endpoint_id=endpoint.id,
            source=payload.source.lower(),
            event_type=payload.event_type.lower(),
            event_category=event_category,
            severity=normalized_severity,
            event_name=payload.event_name,
            occurred_at=occurred_at,
            raw_payload=payload.payload,
            normalized_summary=normalized_summary,
        )
        detection_result = self._run_detection(endpoint=endpoint, raw_event=event)
        return EventIngestionResponse(
            event_id=event.id,
            endpoint_id=endpoint.id,
            event_category=event_category,
            severity=normalized_severity,
            normalized_summary=normalized_summary,
            detection=detection_result,
        )

    def list_endpoints(self) -> list[EndpointResponse]:
        """Return the registered monitored endpoints."""
        endpoints = self._endpoint_repository.list_all()
        return [EndpointResponse.model_validate(endpoint) for endpoint in endpoints]

    def _run_detection(self, *, endpoint, raw_event) -> DetectionResult | None:
        """Run detection if the module is wired into the ingestion pipeline."""
        if self._detection_service is None:
            return None
        return self._detection_service.process_event(endpoint=endpoint, raw_event=raw_event)

    @staticmethod
    def normalize_severity(severity: str) -> str:
        """Map vendor-specific severity labels to a stable internal scale."""
        return SEVERITY_MAP.get(severity.strip().lower(), "medium")

    @staticmethod
    def categorize_event(event_type: str, source: str) -> str:
        """Map raw event metadata to a normalized investigation category."""
        event_key = event_type.strip().lower()
        source_key = source.strip().lower()
        return CATEGORY_MAP.get(event_key) or CATEGORY_MAP.get(source_key) or "system_activity"

    @staticmethod
    def build_summary(
        *,
        hostname: str,
        event_name: str,
        source: str,
        severity: str,
        event_category: str,
    ) -> str:
        """Create a concise normalized event summary for investigations."""
        return (
            f"Endpoint '{hostname}' reported '{event_name}' from source '{source}' "
            f"with {severity} severity in category '{event_category}'."
        )
