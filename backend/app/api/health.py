"""Health check endpoints for service monitoring."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness probe")
async def health_check() -> dict[str, str]:
    """Return a lightweight liveness signal for the API."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def readiness_check() -> dict[str, str]:
    """Return a readiness signal for orchestrators and load balancers."""
    return {"status": "ready"}
