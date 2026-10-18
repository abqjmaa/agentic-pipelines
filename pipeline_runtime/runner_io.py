"""Atomic artifact writes and stable file identities for runner components.
Uses filesystem replacement and hashes; callers own promotion authorization.
Shared by orchestration, candidate processing and report persistence.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path



def entity_id(path: Path, root: Path) -> str:
    return hashlib.sha256(path.relative_to(root).as_posix().encode("utf-8")).hexdigest()[:24]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary_name).replace(path)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()
