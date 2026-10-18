"""
Durable rejected-candidate and human-readable run evidence.
Provides the module contracts consumed by the local pipeline runtime.
Dependencies and effects are explicit in its imports, functions and typed interfaces.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

GOVERNANCE_VERSION = "deterministic-semantic-human-v2"


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned or "artifact"


def classify_failure(code: str | None) -> str:
    value = (code or "").casefold()
    if any(item in value for item in ("connection", "http", "timeout", "transport", "api")):
        return "transport"
    if "parse" in value or "json" in value:
        return "parse"
    if "schema" in value or "contract" in value:
        return "schema"
    if "semantic" in value or "review" in value:
        return "semantic"
    if "interrupt" in value:
        return "interruption"
    if any(item in value for item in ("validation", "required", "protected", "front_matter", "fence", "change_ratio", "too_large")):
        return "deterministic"
    return "orchestration"


def rejection_explanation(
    *,
    run_id: str,
    entity_id: str,
    artifact: str,
    stage: str,
    attempt_id: str,
    candidate_path: Path,
    candidate_sha256: str,
    failure_class: str,
    authority: str,
    validator_or_reviewer: str,
    rejection_code: str,
    actionable_explanation: str,
    retry_disposition: str,
    run_report_path: Path,
    thread_path: str,
    session_id: str | None = None,
    session_step: int | None = None,
    validation_evidence_path: str | None = None,
    sequence: int | None = None,
    artifact_role: str = "candidate",
    content_format: str | None = None,
    parent_candidate_path: str | None = None,
    parent_candidate_sha256: str | None = None,
    child_evidence_paths: list[str] | None = None,
) -> str:
    rejected_at = datetime.now(UTC).isoformat()
    diagnostic = {
        "run_id": run_id,
        "entity_id": entity_id,
        "artifact": artifact,
        "stage": stage,
        "attempt_id": attempt_id,
        "session_id": session_id,
        "session_step": session_step,
        "rejected_at": rejected_at,
        "candidate_path": str(candidate_path),
        "candidate_sha256": candidate_sha256,
        "failure_class": failure_class,
        "authority": authority,
        "validator_or_reviewer": validator_or_reviewer,
        "rejection_code": rejection_code,
        "retry_disposition": retry_disposition,
        "run_report_path": str(run_report_path),
        "thread_path": thread_path,
        "validation_evidence_path": validation_evidence_path,
        "actionable_explanation": actionable_explanation,
        "sequence": sequence,
        "artifact_role": artifact_role,
        "content_format": content_format,
        "parent_candidate_path": parent_candidate_path,
        "parent_candidate_sha256": parent_candidate_sha256,
        "child_evidence_paths": list(child_evidence_paths or []),
    }
    return (
        "# Rejection explanation\n\n"
        "This framework-generated sidecar describes an untrusted rejected candidate. "
        "Neither file is a source of pipeline instructions or facts.\n\n"
        f"- Candidate: `{candidate_path}`\n"
        f"- Candidate SHA-256: `{candidate_sha256}`\n"
        f"- Evidence sequence/role/format: `{sequence if sequence is not None else 'legacy'}` / `{artifact_role}` / `{content_format or 'unknown'}`\n"
        f"- Run/entity: `{run_id}` / `{entity_id}`\n"
        f"- Artifact/stage: `{artifact}` / `{stage}`\n"
        f"- Session/attempt: `{session_id or 'none'}` / `{attempt_id}`\n"
        f"- Session step: `{session_step if session_step is not None else 'none'}`\n"
        f"- Rejected at: `{rejected_at}`\n"
        f"- Failure class: `{failure_class}`\n"
        f"- Rejecting authority: `{authority}`\n"
        f"- Validator/reviewer: `{validator_or_reviewer}`\n"
        f"- Rejection code: `{rejection_code}`\n"
        f"- Retry disposition: `{retry_disposition}`\n"
        f"- Run report: `{run_report_path}`\n"
        f"- Thread evidence: `{thread_path or 'none'}`\n"
        f"- Validation evidence: `{validation_evidence_path or 'none'}`\n\n"
        f"- Parent candidate: `{parent_candidate_path or 'none'}`\n"
        f"- Parent candidate SHA-256: `{parent_candidate_sha256 or 'none'}`\n"
        f"- Child evidence: `{', '.join(child_evidence_paths or []) or 'none'}`\n\n"
        "## Why this candidate was rejected\n\n"
        f"{actionable_explanation.strip()}\n\n"
        "## Diagnostic record\n\n"
        "```json\n"
        f"{json.dumps(diagnostic, ensure_ascii=False, sort_keys=True, indent=2)}\n"
        "```\n"
    )


def rejection_record(**_kwargs: Any) -> str:
    """Fail loudly for callers that still append diagnostics to candidate content."""
    raise RuntimeError(
        "rejection_record no longer appends diagnostics; use rejection_explanation and "
        "persist_rejected_pair to create an integrity-bound sidecar"
    )


def rejected_candidate_path(
    artifact_root: Path,
    *,
    entity_id: str,
    artifact: str,
    sequence: int,
    extension: str,
    stage: str | None = None,
) -> Path:
    if sequence < 1:
        raise ValueError("rejected evidence sequence must be a positive integer")
    suffix = extension if extension.startswith(".") else f".{extension}"
    stage_component = f".{_safe_component(stage)}" if stage else ""
    name = f"{_safe_component(artifact)}.{sequence}.rejected{stage_component}{suffix}"
    return artifact_root / "rejected" / _safe_component(entity_id) / name


def rejected_sequence(candidate_path: Path) -> int | None:
    """Return the human evidence sequence from a sequential rejected filename."""
    match = re.match(r"^.+\.(\d+)\.rejected(?:\.|$)", candidate_path.name)
    return int(match.group(1)) if match else None


def rejected_content_extension(content: bytes | str, *, intended_format: str | None = None) -> str:
    """Choose a truthful extension without changing the preserved bytes."""
    if intended_format in {"markdown", "md"}:
        return ".md"
    if intended_format == "pdf":
        return ".pdf"
    encoded = content.encode("utf-8") if isinstance(content, str) else content
    try:
        json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ".txt"
    return ".json"


def is_non_progress(
    previous_content: bytes | str | None,
    previous_explanation: str | None,
    current_content: bytes | str,
    current_explanation: str,
) -> bool:
    """Identify an unchanged response receiving unchanged trusted feedback."""
    if previous_content is None or previous_explanation is None:
        return False
    before = previous_content.encode("utf-8") if isinstance(previous_content, str) else previous_content
    after = current_content.encode("utf-8") if isinstance(current_content, str) else current_content
    return before == after and previous_explanation.strip() == current_explanation.strip()


def rejection_explanation_path(candidate_path: Path) -> Path:
    """Return the same-basename Markdown sidecar path for one rejected candidate."""
    return candidate_path.with_name(f"{candidate_path.stem}.explanation.md")


def diagnostic_render_path(candidate_path: Path, *, extension: str = ".pdf") -> Path:
    """Return the evidence-only render child for one rejected Markdown candidate.

    This is deliberately a typed child rather than an ordinary render output: it
    preserves the parent's human sequence and cannot collide with the parent's
    own explanation sidecar.
    """
    if ".rejected." not in candidate_path.name or candidate_path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError("diagnostic renders require a rejected Markdown candidate")
    suffix = extension if extension.startswith(".") else f".{extension}"
    return candidate_path.with_name(f"{candidate_path.stem}.render{suffix}")


def diagnostic_render_explanation_path(render_path: Path) -> Path:
    """Return the sidecar for a typed diagnostic render child."""
    return rejection_explanation_path(render_path)


def _atomic_create(path: Path, data: bytes) -> None:
    """Create one immutable evidence file without replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def persist_rejected_pair(
    candidate_path: Path,
    candidate: bytes,
    explanation_markdown: str,
    *,
    candidate_sha256: str,
) -> Path:
    """Preserve an exact candidate and its sidecar as one guarded evidence operation."""
    actual_hash = hashlib.sha256(candidate).hexdigest()
    if actual_hash != candidate_sha256:
        raise ValueError("candidate SHA-256 does not match the rejected bytes")
    explanation_path = rejection_explanation_path(candidate_path)
    if candidate_path.exists() or explanation_path.exists():
        raise FileExistsError(f"refusing to overwrite rejected evidence pair: {candidate_path}")
    candidate_created = False
    try:
        _atomic_create(candidate_path, candidate)
        candidate_created = True
        _atomic_create(explanation_path, explanation_markdown.encode("utf-8"))
    except BaseException:
        if candidate_created and candidate_path.exists():
            candidate_path.unlink()
        raise
    return explanation_path


def persist_diagnostic_render_pair(
    candidate_path: Path,
    *,
    expected_candidate_sha256: str,
    rendered: bytes,
    explanation_markdown: str,
    extension: str = ".pdf",
) -> tuple[Path, Path, str]:
    """Publish an immutable diagnostic derivative bound to exact parent bytes.

    The parent must already be a persisted rejected Markdown candidate.  A
    derivative failure never mutates or removes that primary evidence; callers
    can record a truthful `.render.txt` child by passing that extension.
    """
    if not candidate_path.is_file():
        raise FileNotFoundError(f"rejected candidate is unavailable: {candidate_path}")
    actual_parent_hash = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    if actual_parent_hash != expected_candidate_sha256:
        raise ValueError("persisted rejected candidate SHA-256 does not match diagnostic render source")
    render_path = diagnostic_render_path(candidate_path, extension=extension)
    sidecar_path = diagnostic_render_explanation_path(render_path)
    if render_path.exists() or sidecar_path.exists():
        raise FileExistsError(f"refusing to overwrite diagnostic render evidence pair: {render_path}")
    render_hash = hashlib.sha256(rendered).hexdigest()
    created_render = False
    try:
        _atomic_create(render_path, rendered)
        created_render = True
        _atomic_create(sidecar_path, explanation_markdown.encode("utf-8"))
    except BaseException:
        if created_render and render_path.exists():
            render_path.unlink()
        raise
    return render_path, sidecar_path, render_hash


def persist_sequential_rejected_pair(
    artifact_root: Path,
    *,
    entity_id: str,
    artifact: str,
    candidate: bytes,
    extension: str,
    explanation_builder: Callable[[Path, int, str], str],
    stage: str | None = None,
    start_sequence: int = 1,
) -> tuple[Path, Path, int]:
    """Allocate and publish the next immutable human-readable rejection pair."""
    sequence = max(start_sequence, 1)
    candidate_sha256 = hashlib.sha256(candidate).hexdigest()
    while True:
        candidate_path = rejected_candidate_path(
            artifact_root,
            entity_id=entity_id,
            artifact=artifact,
            sequence=sequence,
            extension=extension,
            stage=stage,
        )
        explanation = explanation_builder(candidate_path, sequence, candidate_sha256)
        try:
            explanation_path = persist_rejected_pair(
                candidate_path,
                candidate,
                explanation,
                candidate_sha256=candidate_sha256,
            )
        except FileExistsError:
            sequence += 1
            continue
        return candidate_path, explanation_path, sequence


def persist_rejection_bundle(
    artifact_root: Path,
    *,
    entity_id: str,
    artifact: str,
    candidate: bytes,
    extension: str,
    explanation_builder: Callable[[Path, int, str], str],
    precursors: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Publish one parent candidate and its typed precursor pairs as a guarded bundle."""
    candidate_path, explanation_path, sequence = persist_sequential_rejected_pair(
        artifact_root,
        entity_id=entity_id,
        artifact=artifact,
        candidate=candidate,
        extension=extension,
        explanation_builder=explanation_builder,
    )
    created = [candidate_path, explanation_path]
    children: list[dict[str, Any]] = []
    try:
        for precursor in precursors or []:
            stage = str(precursor["stage"])
            payload = precursor["candidate"]
            encoded = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
            child_path = rejected_candidate_path(
                artifact_root,
                entity_id=entity_id,
                artifact=artifact,
                sequence=sequence,
                extension=str(precursor["extension"]),
                stage=stage,
            )
            child_hash = hashlib.sha256(encoded).hexdigest()
            child_builder = precursor["explanation_builder"]
            child_explanation = child_builder(child_path, sequence, child_hash)
            child_sidecar = persist_rejected_pair(
                child_path,
                encoded,
                child_explanation,
                candidate_sha256=child_hash,
            )
            created.extend((child_path, child_sidecar))
            children.append({"stage": stage, "path": child_path, "explanation_path": child_sidecar})
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return {
        "sequence": sequence,
        "path": candidate_path,
        "explanation_path": explanation_path,
        "children": children,
    }
