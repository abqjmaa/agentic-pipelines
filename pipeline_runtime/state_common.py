"""Shared SQLite schema version, errors and UTC timestamps.
Provides pure metadata helpers used by migration and transactional state modules.
Does not open databases or mutate repository configuration.
"""
from __future__ import annotations

from datetime import UTC, datetime

SCHEMA_VERSION = 5


class StateError(RuntimeError):
    """State is incompatible, locked, or cannot make the requested transition."""


def _now() -> datetime:
    return datetime.now(UTC)


def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat()
