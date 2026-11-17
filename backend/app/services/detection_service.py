"""Detection and correlation service."""

from dataclasses import dataclass

from app.models.endpoint import Endpoint
from app.models.raw_event import RawEvent
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.detection import AlertResponse, DetectionResult, IncidentResponse


@dataclass
class DetectionRuleMatch:
    """Represents a matched detection rule."""

    rule_name: str
    title: str
    description: str
    severity: str
    correlation_key: str
    mitre_technique: str | None


class DetectionService:
    """Create alerts from raw events and correlate them into incidents."""

    def __init__(
        self,
        alert_repository: AlertRepository,
        incident_repository: IncidentRepository,
    ) -> None:
        self._alert_repository = alert_repository
        self._incident_repository = incident_repository

    def process_event(self, *, endpoint: Endpoint, raw_event: RawEvent) -> DetectionResult:
        """Evaluate a raw event and create alerts/incidents when rules match."""
        match = self._match_rule(endpoint=endpoint, raw_event=raw_event)
        if match is None:
            return DetectionResult(
                alert=None,
                incident=None,
                matched_rule=None,
                correlation_key=None,
            )

        alert = self._alert_repository.create(
            raw_event_id=raw_event.id,
            endpoint_id=raw_event.endpoint_id,
            title=match.title,
            description=match.description,
            severity=match.severity,
            rule_name=match.rule_name,
            correlation_key=match.correlation_key,
            mitre_technique=match.mitre_technique,
        )

        incident = self._incident_repository.find_open_by_correlation(
            endpoint_id=raw_event.endpoint_id,
            correlation_key=match.correlation_key,
            occurred_at=raw_event.occurred_at,
        )
        if incident is None:
            incident = self._incident_repository.create(
                endpoint_id=raw_event.endpoint_id,
                title=match.title,
                summary=match.description,
                severity=match.severity,
                correlation_key=match.correlation_key,
                first_event_at=raw_event.occurred_at,
                created_by_alert_id=alert.id,
            )
        else:
            incident = self._incident_repository.update_correlation(
                incident,
                severity=match.severity,
                summary=match.description,
                last_event_at=raw_event.occurred_at,
            )

        alert = self._alert_repository.assign_to_incident(alert, incident.id)
        return DetectionResult(
            alert=AlertResponse.model_validate(alert),
            incident=IncidentResponse.model_validate(incident),
            matched_rule=match.rule_name,
            correlation_key=match.correlation_key,
        )

    def list_alerts(self) -> list[AlertResponse]:
        """Return all alerts."""
        return [AlertResponse.model_validate(alert) for alert in self._alert_repository.list_all()]

    def list_incidents(self) -> list[IncidentResponse]:
        """Return all incidents."""
        return [IncidentResponse.model_validate(incident) for incident in self._incident_repository.list_all()]

    def _match_rule(self, *, endpoint: Endpoint, raw_event: RawEvent) -> DetectionRuleMatch | None:
        payload_text = str(raw_event.raw_payload).lower()
        source = raw_event.source.lower()
        event_name = raw_event.event_name.lower()
        category = raw_event.event_category.lower()
        severity = raw_event.severity.lower()

        if "credential dumping" in event_name or "lsass" in payload_text:
            return DetectionRuleMatch(
                rule_name="credential_access_indicator",
                title="Credential Access Indicator",
                description=(
                    f"Endpoint {endpoint.hostname} generated telemetry suggesting credential access or "
                    "LSASS targeting."
                ),
                severity="critical",
                correlation_key="credential_access:lsass",
                mitre_technique="T1003",
            )

        if (
            "powershell" in source
            and ("-enc" in payload_text or "frombase64string" in payload_text)
        ):
            return DetectionRuleMatch(
                rule_name="suspicious_powershell_encoded_command",
                title="Suspicious PowerShell Encoded Command",
                description=(
                    f"Endpoint {endpoint.hostname} executed a PowerShell event containing encoded "
                    "or obfuscated command indicators."
                ),
                severity="high",
                correlation_key="script_execution:powershell_encoded",
                mitre_technique="T1059.001",
            )

        if category == "authentication" and severity in {"high", "critical"}:
            return DetectionRuleMatch(
                rule_name="high_risk_authentication_activity",
                title="High-Risk Authentication Activity",
                description=(
                    f"Endpoint {endpoint.hostname} reported a high-severity authentication event "
                    f"named '{raw_event.event_name}'."
                ),
                severity="high" if severity == "high" else "critical",
                correlation_key="authentication:high_risk",
                mitre_technique="T1110",
            )

        if category in {"registry_activity", "file_activity"} and severity == "critical":
            return DetectionRuleMatch(
                rule_name="critical_system_artifact_change",
                title="Critical System Artifact Change",
                description=(
                    f"Endpoint {endpoint.hostname} reported a critical {category} event named "
                    f"'{raw_event.event_name}'."
                ),
                severity="critical",
                correlation_key=f"{category}:critical_change",
                mitre_technique="T1112" if category == "registry_activity" else "T1565.001",
            )

        return None
