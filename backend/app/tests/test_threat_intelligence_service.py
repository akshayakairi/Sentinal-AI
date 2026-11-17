"""Tests for incident threat-intelligence enrichment."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.threat_intelligence import ThreatIntelligenceRequest
from app.services.threat_intelligence import CveRecord, ThreatIntelligenceProviderError
from app.services.threat_intelligence_service import ThreatIntelligenceService


@dataclass
class FakeIncident:
    id: str = "incident-1"


@dataclass
class FakeAlert:
    mitre_technique: str | None


class FakeIncidentRepository:
    def get_by_id(self, incident_id: str):
        return FakeIncident() if incident_id == "incident-1" else None


class FakeAlertRepository:
    def list_by_incident(self, incident_id: str):
        return [FakeAlert("T1059.001"), FakeAlert("T1059.001"), FakeAlert(None)]


class FakeCveProvider:
    def get_cve(self, cve_id: str) -> CveRecord:
        if cve_id == "CVE-2026-9999":
            raise ThreatIntelligenceProviderError("Unavailable")
        return CveRecord(
            cve_id=cve_id,
            description="Example vulnerability.",
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_modified_at=None,
            cvss_version="3.1",
            cvss_score=9.8,
            cvss_severity="CRITICAL",
            reference_urls=["https://example.test/advisory"],
            source_url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
        )


def build_service() -> ThreatIntelligenceService:
    return ThreatIntelligenceService(
        FakeIncidentRepository(),  # type: ignore[arg-type]
        FakeAlertRepository(),  # type: ignore[arg-type]
        FakeCveProvider(),
    )


def test_enrich_combines_mitre_and_cve_data() -> None:
    result = build_service().enrich(
        "incident-1", ThreatIntelligenceRequest(cve_ids=["cve-2026-1234"])
    )

    assert result.mitre_techniques[0].technique_id == "T1059.001"
    assert result.cves[0].cve_id == "CVE-2026-1234"
    assert result.cves[0].cvss_score == 9.8


def test_enrich_returns_partial_result_when_cve_is_unavailable() -> None:
    result = build_service().enrich(
        "incident-1", ThreatIntelligenceRequest(cve_ids=["CVE-2026-9999"])
    )

    assert result.cves == []
    assert result.unavailable_cve_ids == ["CVE-2026-9999"]
