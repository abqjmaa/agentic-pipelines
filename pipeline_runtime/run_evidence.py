"""Assemble structured run metrics and readable Markdown narratives.
Consumes persisted state/evidence and preserves governance and rejection links.
Reads retained artifact files for hashes; callers own report persistence.
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

from .rejection_evidence import GOVERNANCE_VERSION, classify_failure, rejection_explanation_path, rejected_sequence

def execution_status(run: Mapping[str, Any], attempt_count: int) -> str:
    raw = str(run.get("status") or "running")
    if raw == "running":
        return "running"
    if raw == "interrupted":
        return "interrupted"
    if raw == "bounded_stop":
        return "bounded_stop"
    if raw == "failed":
        return "failed"
    processed = int(run.get("processed") or 0)
    accepted = int(run.get("accepted") or 0)
    quarantined = int(run.get("quarantined") or 0)
    if processed == 0 and attempt_count == 0:
        return "no_op"
    if accepted and quarantined:
        return "partially_succeeded"
    if quarantined or not accepted:
        return "failed"
    return "succeeded"


def build_run_evidence(
    *,
    pipeline_id: str,
    run_evidence: Mapping[str, Any],
    state_summary: Mapping[str, int],
    performance: Mapping[str, Any],
    failure_cohorts: list[dict[str, Any]],
) -> dict[str, Any]:
    run = dict(run_evidence["run"])
    attempts = [dict(item) for item in run_evidence.get("attempts", [])]
    rejected = [item for item in attempts if item.get("status") == "rejected" or item.get("artifact_path")]
    statuses = [str(item.get("error_detail") or "") for item in rejected]
    repeated_feedback = len(statuses) - len(set(statuses))
    retry_count = 0
    seen: set[tuple[str, str]] = set()
    attempts_by_entity: dict[str, list[dict[str, Any]]] = {}
    for item in attempts:
        key = (str(item.get("entity_id")), str(item.get("stage")))
        if key in seen:
            retry_count += 1
        seen.add(key)
        attempts_by_entity.setdefault(str(item.get("entity_id")), []).append(item)
    accepted = int(run.get("accepted") or 0)
    processed = int(run.get("processed") or 0)
    entity_rows = {str(item.get("id")): item for item in run_evidence.get("entities", [])}
    first_pass_accepted = sum(
        1
        for entity_id, rows in attempts_by_entity.items()
        if entity_rows.get(entity_id, {}).get("state") in {"accepted", "promoted"}
        and not any(row.get("status") == "rejected" for row in rows)
        and len({str(row.get("stage")) for row in rows}) == len(rows)
    )
    repair_dependent = sum(
        1
        for entity_id, rows in attempts_by_entity.items()
        if entity_rows.get(entity_id, {}).get("state") in {"accepted", "promoted"}
        and any(str(row.get("stage")) == "repair" for row in rows)
    )
    prompt_growth = 0
    changing_feedback = 0
    for rows in attempts_by_entity.values():
        request_sizes = [int(row["request_bytes"]) for row in rows if isinstance(row.get("request_bytes"), int)]
        if len(request_sizes) > 1:
            prompt_growth += max(request_sizes[-1] - request_sizes[0], 0)
        reasons = [str(row.get("error_detail")) for row in rows if row.get("error_detail")]
        if len(set(reasons)) > 1:
            changing_feedback += len(set(reasons)) - 1
    token_total = sum(
        int(row.get("prompt_tokens") or 0) + int(row.get("completion_tokens") or 0)
        for row in attempts
    )
    elapsed_seconds = float(performance.get("elapsed_seconds") or 0)
    derived = {
        **dict(performance),
        "attempt_count": len(attempts),
        "retry_attempt_count": retry_count,
        "rejected_attempt_count": len(rejected),
        "repeated_feedback_count": max(repeated_feedback, 0),
        "changing_feedback_count": changing_feedback,
        "first_pass_yield": first_pass_accepted / processed if processed else None,
        "repair_dependent_acceptance_count": repair_dependent,
        "prompt_growth_bytes": prompt_growth,
        "model_tokens": token_total or "unknown unless supplied by provider evidence",
        "calls_per_accepted_artifact": len(attempts) / accepted if accepted else None,
        "tokens_per_accepted_artifact": token_total / accepted if accepted and token_total else None,
        "seconds_per_accepted_artifact": elapsed_seconds / accepted if accepted else None,
        "non_progress_count": max(repeated_feedback, 0),
        "deterministic_work_sent_to_inference": "unknown without a stage authority declaration linked into runtime evidence",
        "suspected_false_rejection_count": "unknown without an independent evaluation set",
    }
    for item in attempts:
        item["attempt_id"] = item.get("id")
        item["failure_class"] = item.get("failure_class") or ("none" if item.get("status") == "completed" else classify_failure(item.get("error_code")))
        item["authority"] = item.get("authority") or "none"
        item["validator_or_reviewer"] = item.get("validator_name")
        item["explanation"] = item.get("error_detail")
        artifact_value = item.get("artifact_path")
        if artifact_value:
            sidecar = rejection_explanation_path(Path(str(artifact_value)))
            item["explanation_path"] = str(sidecar) if sidecar.is_file() else None
        else:
            item["explanation_path"] = None
    status = execution_status(run, len(attempts))
    learning = "pending" if retry_count or rejected or int(run.get("quarantined") or 0) else "not_required"
    observations = [
        f"The run recorded {len(attempts)} model attempt(s), {retry_count} retry attempt(s), and {len(rejected)} rejected artifact(s).",
        f"Execution resolved as {status}; the runtime originally recorded {run.get('status')}.",
    ]
    if repeated_feedback:
        observations.append(f"Identical rejection feedback recurred {repeated_feedback} time(s).")
    if changing_feedback:
        observations.append(f"Rejection feedback changed {changing_feedback} time(s) within entity trajectories.")
    return {
        "schema_version": 5,
        "governance_version": GOVERNANCE_VERSION,
        "pipeline_id": pipeline_id,
        "run_id": run["id"],
        "execution_status": status,
        "learning_status": learning,
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "checkpointed_at": datetime.now(UTC).isoformat(),
        "reconciled": False,
        "summary": {"state": dict(state_summary), "run": run, "failure_cohorts": failure_cohorts},
        "state": dict(state_summary),
        "performance": derived,
        "failure_cohorts": failure_cohorts,
        "attempts": attempts,
        "rejected_artifacts": [
            {
                "attempt_id": item.get("id"),
                "entity_id": item.get("entity_id"),
                "path": item.get("artifact_path"),
                "explanation_path": item.get("explanation_path"),
                "evidence_format": "sidecar" if item.get("explanation_path") else "legacy_appended",
                "sequence": rejected_sequence(Path(str(item["artifact_path"]))) if item.get("artifact_path") else None,
                "artifact_role": "candidate",
                "content_format": Path(str(item["artifact_path"])).suffix.removeprefix(".") if item.get("artifact_path") else None,
                "parent_candidate_path": None,
                "parent_candidate_sha256": None,
                "child_evidence_paths": [],
                "candidate_sha256": (
                    hashlib.sha256(Path(str(item["artifact_path"])).read_bytes()).hexdigest()
                    if item.get("artifact_path") and Path(str(item["artifact_path"])).is_file()
                    else None
                ),
                "explanation": item.get("error_detail"),
            }
            for item in rejected
        ],
        "observations": observations,
        "metrics": derived,
        "hypotheses": [],
        "recommendations": [],
    }


def _cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_run_markdown(data: Mapping[str, Any], machine_path: Path) -> str:
    lines = [
        f"# Pipeline Run {data['run_id']}",
        "",
        f"- Pipeline: `{data['pipeline_id']}`",
        f"- Governance: `{data['governance_version']}`",
        f"- Execution status: `{data['execution_status']}`",
        f"- Learning status: `{data['learning_status']}`",
        f"- Started: `{_cell(data.get('started_at'))}`",
        f"- Finished: `{_cell(data.get('finished_at'))}`",
        f"- Machine report: `{machine_path}`",
        "",
        "## Outcome summary",
        "",
        f"State counts: `{json.dumps(data['summary']['state'], sort_keys=True)}`",
        "",
        "## Attempts and retries",
        "",
        "| Attempt | Entity | Stage | Status | Failure class | Authority | Reason | Rejected artifact | Explanation sidecar | Thread |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in data["attempts"]:
        lines.append(
            "| " + " | ".join(
                _cell(value)
                for value in (
                    item.get("id"),
                    item.get("entity_id"),
                    item.get("stage"),
                    item.get("status"),
                    item.get("failure_class"),
                    item.get("authority"),
                    item.get("explanation"),
                    item.get("artifact_path"),
                    item.get("explanation_path"),
                    item.get("thread_path"),
                )
            ) + " |"
        )
    if not data["attempts"]:
        lines.append("| — | — | — | no model attempts | none | none | — | — | — | — |")
    lines.extend(["", "## Observations", ""])
    lines.extend(f"- {item}" for item in data["observations"])
    lines.extend(["", "## Deterministic metrics", "", "```json", json.dumps(data["metrics"], ensure_ascii=False, sort_keys=True, indent=2), "```"])
    lines.extend(
        [
            "",
            "## Root-cause hypotheses",
            "",
            "No model-generated hypotheses have been approved for this report." if not data["hypotheses"] else json.dumps(data["hypotheses"], ensure_ascii=False, indent=2),
            "",
            "## Recommendations",
            "",
            "No change is automatically authorized. Review the trajectory and create an approved plan for any modification." if not data["recommendations"] else json.dumps(data["recommendations"], ensure_ascii=False, indent=2),
            "",
            "Observations and metrics are recorded facts or deterministic calculations. Hypotheses and recommendations are advisory.",
            "",
        ]
    )
    return "\n".join(lines)
