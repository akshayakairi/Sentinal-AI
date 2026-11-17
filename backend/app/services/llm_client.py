"""OpenAI-compatible language model client abstractions."""

import json
from typing import Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.services.knowledge_base import KnowledgeDocument


class GeneratedReasoning(BaseModel):
    """Validated language model output used by the reasoning service."""

    summary: str = Field(min_length=1, max_length=4000)
    assessment: str = Field(min_length=1, max_length=4000)
    recommended_actions: list[str] = Field(min_length=1, max_length=10)


class ReasoningGenerator(Protocol):
    """Generates an investigation explanation from supplied evidence only."""

    def generate(self, incident, alerts, documents: list[KnowledgeDocument], question: str | None) -> GeneratedReasoning:
        """Return validated, grounded reasoning content."""


class OpenAICompatibleReasoningGenerator:
    """Synchronous OpenAI Chat Completions client with strict JSON output."""

    def __init__(self, settings: Settings) -> None:
        if not all((settings.llm_base_url, settings.llm_api_key, settings.llm_model)):
            raise ValueError("LLM base URL, API key, and model must all be configured.")
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._model = settings.llm_model
        self._timeout = settings.llm_timeout_seconds

    def generate(self, incident, alerts, documents: list[KnowledgeDocument], question: str | None) -> GeneratedReasoning:
        """Ask the configured model for JSON constrained to the supplied evidence."""
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._build_context(incident, alerts, documents, question)},
                ],
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        try:
            content = response.json()["choices"][0]["message"]["content"]
            return GeneratedReasoning.model_validate(json.loads(content))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as error:
            raise ValueError("LLM response did not match the SentinelAI reasoning schema.") from error

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a cybersecurity investigation assistant. Use only the supplied incident evidence "
            "and knowledge sources. Do not claim containment was performed or invent facts. Return JSON "
            "with keys summary, assessment, and recommended_actions."
        )

    @staticmethod
    def _build_context(incident, alerts, documents: list[KnowledgeDocument], question: str | None) -> str:
        alert_lines = [
            f"- {alert.title}: {alert.description} (MITRE: {alert.mitre_technique or 'unknown'})"
            for alert in alerts
        ]
        source_lines = [f"- {document.title}: {document.content}" for document in documents]
        return "\n".join(
            [
                f"Incident: {incident.title}",
                f"Summary: {incident.summary}",
                f"Severity: {incident.severity}",
                "Alerts:",
                *alert_lines,
                "Retrieved knowledge:",
                *source_lines,
                f"Analyst question: {question or 'Provide an initial investigation assessment.'}",
            ]
        )
