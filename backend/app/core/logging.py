"""Logging configuration for the SentinelAI backend."""

import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure process-wide logging once during startup."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
