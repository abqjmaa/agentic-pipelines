"""Candidate processing, rejected evidence and validated promotion.
Composes with PipelineRunner through its definition, store and stage interfaces.
May persist artifacts or call configured inference only through runner contracts.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any


from .api import InferenceError
from .evidence import persist_sequential_rejected_pair, rejected_content_extension, rejection_explanation
from .prompts import PromptError
from .state import StateError

from .runner_io import _atomic_write, digest


class RunnerCandidatesMixin:
    def _write_artifact(self, kind: str, entity: str, name: str, content: str | bytes) -> Path:
        path = self.definition.artifact_root / kind / entity / name
        encoded = content.encode("utf-8") if isinstance(content, str) else content
        _atomic_write(path, encoded)
        return path


    def _write_rejected_candidate(
        self,
        content: str,
        *,
        run_id: str,
        entity: str,
        artifact: str,
        stage: str,
        attempt_id: str,
        extension: str,
        failure_class: str,
        authority: str,
        validator_or_reviewer: str,
        rejection_code: str,
        explanation: str,
        retry_disposition: str,
        thread: str,
    ) -> Path:
        encoded = content.encode("utf-8")
        attempt_evidence = self.store.attempt_evidence(attempt_id)
        attempt_row = attempt_evidence["attempt"]
        requested = extension.removeprefix(".")
        intended_format = "markdown" if requested in {"md", "markdown"} else "pdf" if requested == "pdf" else None
        truthful_extension = rejected_content_extension(encoded, intended_format=intended_format)

        def build_explanation(path: Path, sequence: int, candidate_sha256: str) -> str:
            return rejection_explanation(
                run_id=run_id,
                entity_id=entity,
                artifact=artifact,
                stage=stage,
                attempt_id=attempt_id,
                candidate_path=path,
                candidate_sha256=candidate_sha256,
                failure_class=failure_class,
                authority=authority,
                validator_or_reviewer=validator_or_reviewer,
                rejection_code=rejection_code,
                actionable_explanation=explanation,
                retry_disposition=retry_disposition,
                run_report_path=self.definition.report_root / f"{run_id}.md",
                thread_path=thread,
                session_id=attempt_row.get("session_id"),
                session_step=attempt_row.get("session_step"),
                validation_evidence_path=attempt_evidence.get("validation_evidence_path"),
                sequence=sequence,
                artifact_role="candidate",
                content_format=truthful_extension.removeprefix("."),
            )
        try:
            path, _sidecar, _sequence = persist_sequential_rejected_pair(
                self.definition.artifact_root,
                entity_id=entity,
                artifact=artifact,
                candidate=encoded,
                extension=truthful_extension,
                explanation_builder=build_explanation,
            )
        except (FileExistsError, OSError, ValueError) as exc:
            raise StateError(f"failed to preserve rejected evidence pair for {entity}/{artifact}: {exc}") from exc
        self.store.finish_attempt(
            attempt_id,
            "rejected",
            thread=thread or None,
            artifact=str(path),
            error=(rejection_code, explanation),
            response_bytes=len(encoded),
            failure_class=failure_class,
            authority=authority,
            validator_name=validator_or_reviewer,
            retry_disposition=retry_disposition,
        )
        self.report(run_id)
        return path


    def _promote(self, entity: str, source_path: Path, expected_hash: str, accepted_path: Path) -> str:
        if digest(source_path) != expected_hash:
            raise StateError("source changed after discovery; refusing promotion")
        backup = self.definition.promotion.backup_root / entity / f"{expected_hash}.bak"
        if not backup.exists():
            _atomic_write(backup, source_path.read_bytes())
        candidate = accepted_path.read_bytes()
        candidate_hash = hashlib.sha256(candidate).hexdigest()
        promotion_id = f"promotion-{uuid.uuid4().hex[:16]}"
        self.store.prepare_promotion(promotion_id, entity, expected_hash, candidate_hash, str(backup))
        temporary = source_path.parent / f".{source_path.name}.{uuid.uuid4().hex}.promote"
        try:
            _atomic_write(temporary, candidate)
            temporary.replace(source_path)
            self.store.finish_promotion(promotion_id, "completed")
            return candidate_hash
        except OSError:
            self.store.finish_promotion(promotion_id, "failed")
            raise


    def _process(self, row: Any, run_id: str, owner: str) -> None:
        entity = row["id"]
        source_path = Path(row["source_path"])
        expected_hash = row["source_hash"]
        if source_path.stat().st_size > self.definition.runtime.max_source_bytes:
            self.store.set_outcome(entity, "quarantined", error=("source_too_large", f"source exceeds {self.definition.runtime.max_source_bytes} bytes"))
            return
        if digest(source_path) != expected_hash:
            self.store.set_outcome(entity, "quarantined", error=("source_changed", "source changed after discovery"))
            return
        source = source_path.read_text(encoding="utf-8")
        revision = expected_hash[:16]
        self.store.lease(entity, run_id, owner, self.definition.runtime.lease_seconds)
        snapshot = self._write_artifact("source", entity, f"{revision}.md", source)
        worker = self.definition.stages["worker"]
        last_thread = ""
        try:
            result, attempt, last_thread = self._invoke(worker, self._context(source), run_id=run_id, entity=entity, revision=revision)
            if result["status"] != "candidate" or not isinstance(result.get("candidate"), str):
                explanation = str(result.get("reason") or "worker returned unable")
                rejected = self._write_rejected_candidate(
                    json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    run_id=run_id,
                    entity=entity,
                    artifact=worker.name,
                    stage=worker.name,
                    attempt_id=attempt,
                    extension="json",
                    failure_class="semantic",
                    authority="semantic_model",
                    validator_or_reviewer="worker_result_contract",
                    rejection_code="worker_unable",
                    explanation=explanation,
                    retry_disposition="quarantine",
                    thread=last_thread,
                )
                self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=("worker_unable", explanation), thread=last_thread, prompt_hash=self.contract_hash, evidence=str(snapshot))
                return
            candidate = str(result["candidate"])
            if len(candidate.encode("utf-8")) > self.definition.runtime.max_candidate_bytes:
                explanation = f"candidate exceeds {self.definition.runtime.max_candidate_bytes} bytes"
                rejected = self._write_rejected_candidate(
                    candidate,
                    run_id=run_id,
                    entity=entity,
                    artifact="worker",
                    stage="candidate_size_validation",
                    attempt_id=attempt,
                    extension="md",
                    failure_class="deterministic",
                    authority="deterministic",
                    validator_or_reviewer="max_candidate_bytes",
                    rejection_code="candidate_too_large",
                    explanation=explanation,
                    retry_disposition="quarantine",
                    thread=last_thread,
                )
                self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=("candidate_too_large", explanation), thread=last_thread, prompt_hash=self.contract_hash)
                return
            staged = self._write_artifact("staged", entity, f"{attempt}.md", candidate)
            evidence, evidence_path = self._validate_candidate(run_id, entity, attempt, source, candidate)
            if not evidence.passed:
                explanation = ", ".join(evidence.failure_codes)
                rejected = self._write_rejected_candidate(
                    candidate,
                    run_id=run_id,
                    entity=entity,
                    artifact=worker.name,
                    stage="deterministic_validation",
                    attempt_id=attempt,
                    extension="md",
                    failure_class="deterministic",
                    authority="deterministic",
                    validator_or_reviewer="pipeline_validation",
                    rejection_code=evidence.failure_codes[0],
                    explanation=explanation,
                    retry_disposition="semantic_repair" if self.definition.stages.get("repair") else "quarantine",
                    thread=last_thread,
                )
                repaired, repair_attempt, repair_thread = self._repair(source, candidate, list(evidence.failure_codes), run_id=run_id, entity=entity, revision=revision)
                if repaired is None:
                    self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=(evidence.failure_codes[0], explanation), thread=repair_thread or last_thread, prompt_hash=self.contract_hash, evidence=str(evidence_path))
                    return
                candidate = repaired
                attempt = repair_attempt
                last_thread = repair_thread or last_thread
                staged = self._write_artifact("staged", entity, f"{attempt}.md", candidate)
                evidence, evidence_path = self._validate_candidate(run_id, entity, attempt, source, candidate)
                if not evidence.passed:
                    explanation = ", ".join(evidence.failure_codes)
                    rejected = self._write_rejected_candidate(
                        candidate,
                        run_id=run_id,
                        entity=entity,
                        artifact="repair",
                        stage="deterministic_validation",
                        attempt_id=attempt,
                        extension="md",
                        failure_class="deterministic",
                        authority="deterministic",
                        validator_or_reviewer="pipeline_validation",
                        rejection_code=evidence.failure_codes[0],
                        explanation=explanation,
                        retry_disposition="quarantine",
                        thread=last_thread,
                    )
                    self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=(evidence.failure_codes[0], explanation), thread=last_thread, evidence=str(evidence_path))
                    return
            review_passed, violations, review_thread = self._semantic_review(source, candidate, evidence, run_id=run_id, entity=entity, revision=revision)
            if not review_passed:
                explanation = json.dumps(violations, ensure_ascii=False)
                rejected = self._write_rejected_candidate(
                    candidate,
                    run_id=run_id,
                    entity=entity,
                    artifact=f"{worker.name}-semantic-review" if attempt.startswith("a-") else "semantic-review",
                    stage="semantic_review",
                    attempt_id=attempt,
                    extension="md",
                    failure_class="semantic",
                    authority="semantic_model",
                    validator_or_reviewer="independent_semantic_review",
                    rejection_code="semantic_review_failed",
                    explanation=explanation,
                    retry_disposition="adjudicate_then_repair_or_quarantine",
                    thread=review_thread or last_thread,
                )
                action, adjudication_thread = self._adjudicate(source, candidate, evidence, violations, run_id=run_id, entity=entity, revision=revision)
                if action != "repair":
                    self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=("semantic_review_failed", f"adjudication={action}; {explanation}"), thread=adjudication_thread or review_thread or last_thread, evidence=str(evidence_path))
                    return
                repaired, repair_attempt, repair_thread = self._repair(source, candidate, violations, run_id=run_id, entity=entity, revision=revision)
                if repaired is None:
                    self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=("semantic_review_failed", explanation), thread=review_thread or last_thread, evidence=str(evidence_path))
                    return
                candidate = repaired
                attempt = repair_attempt
                last_thread = repair_thread or review_thread or last_thread
                staged = self._write_artifact("staged", entity, f"{attempt}.md", candidate)
                evidence, evidence_path = self._validate_candidate(run_id, entity, attempt, source, candidate)
                review_passed, violations, review_thread = self._semantic_review(source, candidate, evidence, run_id=run_id, entity=entity, revision=revision) if evidence.passed else (False, list(evidence.failure_codes), "")
                if not evidence.passed or not review_passed:
                    explanation = json.dumps(violations, ensure_ascii=False)
                    failure_class = "deterministic" if not evidence.passed else "semantic"
                    authority = "deterministic" if not evidence.passed else "semantic_model"
                    rejected = self._write_rejected_candidate(
                        candidate,
                        run_id=run_id,
                        entity=entity,
                        artifact="repair",
                        stage="repair_validation" if not evidence.passed else "semantic_review",
                        attempt_id=attempt,
                        extension="md",
                        failure_class=failure_class,
                        authority=authority,
                        validator_or_reviewer="pipeline_validation" if not evidence.passed else "independent_semantic_review",
                        rejection_code="repair_not_accepted",
                        explanation=explanation,
                        retry_disposition="quarantine",
                        thread=review_thread or last_thread,
                    )
                    self.store.set_outcome(entity, "quarantined", candidate=str(rejected), error=("repair_not_accepted", explanation), thread=review_thread or last_thread, evidence=str(evidence_path))
                    return
            accepted = self._write_artifact("accepted", entity, f"{attempt}.md", candidate)
            state = "accepted"
            new_source_hash = None
            if self.definition.promotion.enabled:
                new_source_hash = self._promote(entity, source_path, expected_hash, accepted)
                state = "promoted"
            self.store.set_outcome(entity, state, candidate=str(staged), accepted=str(accepted), thread=review_thread or last_thread, prompt_hash=self.contract_hash, source_hash=new_source_hash, evidence=str(evidence_path))
        except (InferenceError, PromptError, StateError, OSError) as exc:
            safe = self.client.redact(str(exc)) if self.client is not None else str(exc)
            self.store.set_outcome(entity, "quarantined", error=("processing_error", safe), thread=last_thread or None)
