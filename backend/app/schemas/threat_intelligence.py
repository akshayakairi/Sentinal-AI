"""Schemas for incident threat-intelligence enrichment."""

from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


class ThreatIntelligenceRequest(BaseModel):
    """Optional CVE identifiers an analyst wants to enrich."""

    cve_ids: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("cve_ids")
    @classmethod
    def validate_cve_ids(cls, value: list[str]) -> list[str]:
        """Normalize and validate standard CVE identifiers."""
        normalized = [cve_id.upper().strip() for cve_id in value]
        if len(set(normalized)) != len(normalized):
            raise ValueError("CVE identifiers must be unique.")
        if any(not re.fullmatch(r"CVE-\d{4}-\d{4,}", cve_id) for cve_id in normalized):
            raise ValueError("Each CVE identifier must use the CVE-YYYY-NNNN format.")
        return normalized


class MitreTechniqueEnrichment(BaseModel):
    """MITRE ATT&CK technique referenced by the incident's alerts."""

    technique_id: str
    source_url: str


class CveEnrichment(BaseModel):
    """Normalized vulnerability data returned from NVD."""

    cve_id: str
    description: str
    published_at: datetime | None
    last_modified_at: datetime | None
    cvss_version: str | None
    cvss_score: float | None
    cvss_severity: str | None
    reference_urls: list[str]
    source_url: str


class ThreatIntelligenceResponse(BaseModel):
    """Read-only intelligence context for an incident."""

    incident_id: str
    mitre_techniques: list[MitreTechniqueEnrichment]
    cves: list[CveEnrichment]
    unavailable_cve_ids: list[str]
    sources: list[str]
    disclaimer: str = (
        "Threat intelligence is contextual evidence. Validate applicability to the affected endpoint "
        "before remediation or containment actions."
    )
