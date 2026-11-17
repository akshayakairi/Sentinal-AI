"""Authorization dependency tests."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.dependencies import require_roles


@dataclass
class FakeUser:
    id: str = "user-1"
    email: str = "user@sentinelai.com"
    full_name: str = "SOC User"
    hashed_password: str = "hashed"
    role: str = "viewer"
    is_active: bool = True
    created_at: datetime = datetime.now(timezone.utc)


def test_require_roles_allows_matching_role() -> None:
    dependency = require_roles("admin", "analyst")
    user = FakeUser(role="analyst")

    assert dependency(user) is user  # type: ignore[arg-type]


def test_require_roles_rejects_unmatched_role() -> None:
    dependency = require_roles("admin")

    with pytest.raises(HTTPException) as exc_info:
        dependency(FakeUser(role="viewer"))  # type: ignore[arg-type]

    assert exc_info.value.status_code == 403
