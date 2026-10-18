"""Bounded resumable orchestration composed from focused runner components.
PipelineRunner preserves the public execution, discovery and recovery interface.
Delegates inference, candidate processing, reporting and atomic file operations.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
import uuid
from pathlib import Path
from typing import Any


from .api import InferenceClient
from .definition import PipelineDefinition
from .prompts import OutputSchemas, PromptContract, PromptError, load_prompt
from .state import StateError, StateStore

from .runner_io import _atomic_write, digest, entity_id
from .runner_inference import RunnerInferenceMixin
from .runner_candidates import RunnerCandidatesMixin
from .runner_reports import RunnerReportsMixin


class PipelineRunner(RunnerInferenceMixin, RunnerCandidatesMixin, RunnerReportsMixin):
    def __init__(self, definition: PipelineDefinition, client: InferenceClient | None = None) -> None:
        self.definition = definition
        self.client = client
        self.store = StateStore(definition.state_path)
        self.schemas = OutputSchemas(definition.output_schema_path)
        self.prompts: dict[str, PromptContract] = {}
        self._stage_counts: dict[tuple[str, str, str], int] = {}
        self._session_steps: dict[tuple[str, str, str], int] = {}
        for name, stage in {**definition.stages, **definition.analysis}.items():
            prompt = load_prompt(
                stage.prompt_path,
                expected_id=stage.prompt_id,
                expected_version=stage.prompt_version,
                expected_output=stage.output_schema,
            )
            if prompt.kind != "pipeline-running":
                raise PromptError(f"stage {name} must use a pipeline-running prompt")
            if not self.schemas.has(prompt.output):
                raise PromptError(f"stage {name} references unknown output {prompt.output}")
            self.prompts[name] = prompt
        contract_material = definition.path.read_bytes() + "".join(sorted(prompt.content_hash for prompt in self.prompts.values())).encode("ascii")
        self.contract_hash = hashlib.sha256(contract_material).hexdigest()


    def close(self) -> None:
        self.store.close()


    def discover(self) -> int:
        changed = 0
        excluded_roots = tuple(
            root.resolve()
            for root in (
                self.definition.artifact_root,
                self.definition.thread_root,
                self.definition.report_root,
                self.definition.state_path.parent,
            )
        )
        for path in sorted(self.definition.source_root.glob(self.definition.source_glob)):
            resolved = path.resolve()
            if ".rejected." in path.name or any(resolved == root or root in resolved.parents for root in excluded_roots):
                continue
            if path.is_file() and self.store.upsert_discovered(entity_id(path, self.definition.source_root), str(path), digest(path), self.contract_hash):
                changed += 1
        return changed


    def run(self, maximum: int, runtime_minutes: float, dry_run: bool = False) -> dict[str, Any]:
        if maximum < 1 or runtime_minutes <= 0:
            raise ValueError("run bounds must be positive")
        if dry_run:
            eligible = self.store.eligible(maximum)
            run_id = f"run-{uuid.uuid4().hex[:16]}"
            self.store.start_run(run_id)
            self.store.finish_run(run_id, "completed")
            report = self.report(run_id)
            return {
                "run_id": run_id,
                "status": "dry_run",
                "eligible": len(eligible),
                "entity_ids": [row["id"] for row in eligible],
                "state": self.store.summary(),
                "report": str(report),
                "human_report": str(report.with_suffix(".md")),
            }
        run_id = f"run-{uuid.uuid4().hex[:16]}"
        owner = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        lock_seconds = max(self.definition.runtime.lock_stale_seconds, int(runtime_minutes * 60) + 60)
        self.store.acquire_lock(owner, run_id, lock_seconds)
        for stale_run_id in self.store.reconcile_running_runs():
            self.report(stale_run_id)
        self.store.recover_expired_leases()
        eligible = self.store.eligible(maximum)
        self.store.start_run(run_id)
        started = time.monotonic()
        status = "completed"
        initial_report: Path | None = None
        failure: Exception | None = None
        try:
            # Evidence persistence is a precondition for material work.
            initial_report = self.report(run_id)
            for row in eligible:
                if time.monotonic() - started >= runtime_minutes * 60:
                    status = "bounded_stop"
                    break
                self._process(row, run_id, owner)
                self.report(run_id)
        except KeyboardInterrupt:
            status = "interrupted"
        except Exception as exc:
            status = "failed"
            failure = exc
        finally:
            self.store.finish_run(run_id, status)
            self.store.release_lock(owner, run_id)
        report = self.report(run_id)
        if failure is not None:
            raise failure
        narrative = report.with_suffix(".md")
        return {
            "run_id": run_id,
            "status": status,
            "state": self.store.summary(),
            "report": str(report),
            "human_report": str(narrative),
            "initial_report": str(initial_report) if initial_report else None,
        }


    def retry_cohort(self, report_path: Path, cohort_id: str) -> int:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        cohort = next((item for item in report.get("failure_cohorts", []) if item.get("cohort_id") == cohort_id), None)
        if cohort is None or not isinstance(cohort.get("entity_ids"), list):
            raise ValueError(f"cohort not found: {cohort_id}")
        return self.store.retry_entities([str(item) for item in cohort["entity_ids"]])


    def rollback_entity(self, entity: str) -> Path:
        evidence = self.store.entity(entity)
        if not evidence or evidence["entity"]["state"] != "promoted":
            raise StateError("only a promoted entity can be rolled back")
        promotion = self.store.latest_promotion(entity)
        if not promotion or promotion["status"] != "completed":
            raise StateError("completed promotion evidence is missing")
        source_path = Path(evidence["entity"]["source_path"])
        if digest(source_path) != promotion["candidate_hash"]:
            raise StateError("promoted source changed; refusing rollback")
        backup = Path(promotion["backup_path"])
        if not backup.exists() or digest(backup) != promotion["original_hash"]:
            raise StateError("promotion backup is missing or corrupt")
        _atomic_write(source_path, backup.read_bytes())
        self.store.finish_promotion(promotion["id"], "rolled_back")
        self.store.set_outcome(
            entity,
            "quarantined",
            candidate=evidence["entity"]["candidate_path"],
            accepted=evidence["entity"]["accepted_path"],
            error=("operator_rollback", "promotion was explicitly rolled back"),
            source_hash=promotion["original_hash"],
            evidence=str(backup),
        )
        return source_path
