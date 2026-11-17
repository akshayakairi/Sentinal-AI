"""Incident-level threat-intelligence enrichment service."""

from fastapi import HTTPException, status

from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.schemas.threat_intelligence import (
    CveEnrichment,
    MitreTechniqueEnrichment,
    ThreatIntelligenceRequest,
    ThreatIntelligenceResponse,
)
from app.services.threat_intelligence import CveLookupProvider, ThreatIntelligenceProviderError


class ThreatIntelligenceService:
    """Combine incident evidence with attributable external intelligence."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        alert_repository: AlertRepository,
        cve_provider: CveLookupProvider,
    ) -> None:
        self._incident_repository = incident_repository
        self._alert_repository = alert_repository
        self._cve_provider = cve_provider

    def enrich(self, incident_id: str, request: ThreatIntelligenceRequest) -> ThreatIntelligenceResponse:
        """Return alert-derived ATT&CK and requested CVE intelligence."""
        incident = self._incident_repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident was not found.")

        techniques = sorted({
            alert.mitre_technique
            for alert in self._alert_repository.list_by_incident(incident_id)
            if alert.mitre_technique
        })
        cves = []
        unavailable_cve_ids = []
        for cve_id in request.cve_ids:
            try:
                record = self._cve_provider.get_cve(cve_id)
            except ThreatIntelligenceProviderError:
                unavailable_cve_ids.append(cve_id)
                continue
            cves.append(CveEnrichment(**record.__dict__))

        mitre_enrichment = [
            MitreTechniqueEnrichment(
                technique_id=technique,
                source_url=f"https://attack.mitre.org/techniques/{technique.replace('.', '/')}/",
            )
            for technique in techniques
        ]
        sources = [item.source_url for item in mitre_enrichment] + [item.source_url for item in cves]
        return ThreatIntelligenceResponse(
            incident_id=incident.id,
            mitre_techniques=mitre_enrichment,
            cves=cves,
            unavailable_cve_ids=unavailable_cve_ids,
            sources=sources,
        )
