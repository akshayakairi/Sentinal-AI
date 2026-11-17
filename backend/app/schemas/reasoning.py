"""Schemas for AI-assisted incident reasoning."""

from pydantic import BaseModel, Field


class ReasoningRequest(BaseModel):
    """Optional analyst question that focuses the investigation explanation."""

    question: str | None = Field(default=None, max_length=2000)


class ReasoningSource(BaseModel):
    """Attributable knowledge source returned with a reasoning result."""

    id: str
    title: str
    source_url: str


class IncidentReasoningResponse(BaseModel):
    """Grounded AI-assistance response for a single incident."""

    incident_id: str
    summary: str
    assessment: str
    recommended_actions: list[str]
    sources: list[ReasoningSource]
    model_used: str | None = None
    disclaimer: str = (
        "AI-assisted analysis is advisory. Validate findings and response actions before execution."
    )
