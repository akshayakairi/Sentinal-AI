"""External threat-intelligence provider adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

import httpx


class ThreatIntelligenceProviderError(Exception):
    """Raised when an external intelligence provider cannot return usable data."""


@dataclass(frozen=True)
class CveRecord:
    """Provider-independent CVE intelligence record."""

    cve_id: str
    description: str
    published_at: datetime | None
    last_modified_at: datetime | None
    cvss_version: str | None
    cvss_score: float | None
    cvss_severity: str | None
    reference_urls: list[str]
    source_url: str


class CveLookupProvider(Protocol):
    """Retrieves a normalized CVE record."""

    def get_cve(self, cve_id: str) -> CveRecord:
        """Look up a single CVE identifier."""


class NvdCveLookupProvider:
    """NVD CVE API 2.0 client."""

    def __init__(self, api_url: str, api_key: str | None, timeout_seconds: float) -> None:
        self._api_url = api_url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def get_cve(self, cve_id: str) -> CveRecord:
        """Fetch and normalize a CVE from the NVD API."""
        headers = {"apiKey": self._api_key} if self._api_key else {}
        try:
            response = httpx.get(
                self._api_url,
                params={"cveId": cve_id},
                headers=headers,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            vulnerability = response.json().get("vulnerabilities", [])[0]["cve"]
        except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError) as error:
            raise ThreatIntelligenceProviderError(f"NVD lookup failed for {cve_id}.") from error

        metric = _select_metric(vulnerability.get("metrics", {}))
        cvss_data = metric.get("cvssData", {}) if metric else {}
        return CveRecord(
            cve_id=vulnerability["id"],
            description=_english_description(vulnerability.get("descriptions", [])),
            published_at=_parse_nvd_datetime(vulnerability.get("published")),
            last_modified_at=_parse_nvd_datetime(vulnerability.get("lastModified")),
            cvss_version=cvss_data.get("version"),
            cvss_score=cvss_data.get("baseScore"),
            cvss_severity=cvss_data.get("baseSeverity") or metric.get("baseSeverity") if metric else None,
            reference_urls=[reference["url"] for reference in vulnerability.get("references", []) if "url" in reference],
            source_url=f"https://nvd.nist.gov/vuln/detail/{vulnerability['id']}",
        )


def _english_description(descriptions: list[dict[str, str]]) -> str:
    """Return NVD's English description when available."""
    return next((item["value"] for item in descriptions if item.get("lang") == "en"), "No description available.")


def _select_metric(metrics: dict[str, Any]) -> dict[str, Any] | None:
    """Prefer the newest available CVSS metric."""
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if metric_list := metrics.get(key):
            return metric_list[0]
    return None


def _parse_nvd_datetime(value: str | None) -> datetime | None:
    """Parse NVD ISO 8601 timestamps, accepting a trailing Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
