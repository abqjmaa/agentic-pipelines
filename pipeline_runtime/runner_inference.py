"""Bounded inference sessions, validation, repair and semantic review.
Composes with PipelineRunner through its definition, store and stage interfaces.
May persist artifacts or call configured inference only through runner contracts.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Mapping


from .api import InferenceError, InferenceRequest
from .definition import PromptStage
from .evidence import classify_failure
from .prompts import PromptError
from .state import StateError
from .validators import ValidationEvidence, validate



class RunnerInferenceMixin:
    def _invoke(
        self,
        stage: PromptStage,
        context: Mapping[str, Any],
        *,
        run_id: str,
        entity: str,
        revision: str,
    ) -> tuple[Mapping[str, Any], str, str]:
        prompt = self.prompts[stage.name]
        if self.client is None:
            raise StateError("this operation requires configured local inference")
        count_key = (run_id, entity, stage.name)
        count = self._stage_counts.get(count_key, 0) + 1
        if count > stage.max_attempts:
            raise StateError(f"stage attempt budget exceeded: {stage.name}")
        self._stage_counts[count_key] = count
        inputs = {name: context[name] for name in prompt.inputs if name in context}
        rendered = prompt.render(inputs)
        attempt_id = f"a-{uuid.uuid4().hex[:16]}"
        lane = "independent-review" if stage.name in {"self_review", "reviewer", "adjudicator"} else "worker"
        session_key = (run_id, entity, lane)
        session_step = self._session_steps.get(session_key, 0) + 1
        self._session_steps[session_key] = session_step
        generation = dict(self.client.config.generation)
        self.store.begin_attempt(
            attempt_id,
            run_id,
            entity,
            stage.name,
            prompt.prompt_id,
            prompt.version,
            prompt.content_hash,
            request_bytes=len(rendered.encode("utf-8")),
            prompt_template_bytes=len(prompt.body.encode("utf-8")),
            context_limit=generation.get("num_ctx") if isinstance(generation.get("num_ctx"), int) else None,
            completion_limit=generation.get("num_predict") if isinstance(generation.get("num_predict"), int) else None,
            reasoning_mode=str(generation.get("think", "unspecified")),
            provider=self.client.config.provider,
            model=self.client.config.model,
            generation_config=generation,
            session_id=f"{run_id}-{entity}-{lane}",
            session_step=session_step,
        )
        response = None
        try:
            response = self.client.invoke(
                InferenceRequest(
                    messages=[{"role": "user", "content": rendered}],
                    response_format=self.schemas.schema_for(prompt.output),
                    stage=stage.name,
                    run_id=run_id,
                    entity_id=entity,
                    entity_revision=revision,
                    attempt_id=attempt_id,
                    prompt_template_id=prompt.prompt_id,
                    prompt_template_hash=prompt.content_hash,
                )
            )
            result = self.schemas.validate(prompt.output, response.content)
            thread = str(response.capture_path) if response.capture_path else ""
            self.store.finish_attempt(
                attempt_id,
                "completed",
                thread=thread or None,
                response_bytes=len(response.content.encode("utf-8")),
                failure_class="none",
                authority="semantic_model",
                validator_name=prompt.output,
                retry_disposition="continue_stage",
                transport_attempts=response.attempts,
                transport_retry_events=[dict(item) for item in response.retry_events],
                prompt_tokens=int(response.usage["prompt_eval_count"]) if isinstance(response.usage.get("prompt_eval_count"), int) else None,
                completion_tokens=int(response.usage["eval_count"]) if isinstance(response.usage.get("eval_count"), int) else None,
            )
            return result, attempt_id, thread
        except (InferenceError, PromptError) as exc:
            thread_path = getattr(exc, "capture_path", None)
            safe = self.client.redact(str(exc))
            thread = str(thread_path or (response.capture_path if response and response.capture_path else ""))
            raw_failure = getattr(exc, "raw_content", None)
            if response is not None or raw_failure is not None:
                code = "schema_or_parse_rejection"
                failure_class = "schema" if isinstance(exc, PromptError) else classify_failure(code)
                self._write_rejected_candidate(
                    self.client.redact(response.content if response is not None else str(raw_failure)),
                    run_id=run_id,
                    entity=entity,
                    artifact=stage.name,
                    stage=stage.name,
                    attempt_id=attempt_id,
                    extension="txt",
                    failure_class=failure_class,
                    authority="deterministic",
                    validator_or_reviewer=prompt.output,
                    rejection_code=code,
                    explanation=safe,
                    retry_disposition="stage_retry_or_terminal",
                    thread=thread,
                )
            else:
                self.store.finish_attempt(
                    attempt_id,
                    "failed",
                    thread=thread or None,
                    error=("stage_error", safe),
                    failure_class=classify_failure(str(exc)),
                    authority="none",
                    validator_name="inference_transport",
                    retry_disposition="transport_policy_or_terminal",
                    transport_attempts=getattr(exc, "attempts", None),
                    transport_retry_events=list(getattr(exc, "retry_events", [])),
                )
            raise


    def _context(self, source: str, candidate: str | None = None, evidence: Mapping[str, Any] | None = None, violations: list[Any] | None = None) -> dict[str, Any]:
        return {
            "goal": self.definition.goal,
            "source_entity": source,
            "candidate": candidate,
            "allowed_changes": list(self.definition.allowed_changes),
            "protected_invariants": list(self.definition.protected_invariants),
            "invariants": list(self.definition.protected_invariants),
            "deterministic_evidence": evidence or {},
            "violations": violations or [],
            "review_verdicts": [],
            "allowed_actions": ["repair", "quarantine", "human_required"],
        }


    def _adjudicate(self, source: str, candidate: str, evidence: ValidationEvidence, violations: list[Any], *, run_id: str, entity: str, revision: str) -> tuple[str, str]:
        stage = self.definition.stages.get("adjudicator")
        if stage is None:
            return "repair", ""
        context = self._context(source, candidate, evidence.as_dict(), violations)
        context["review_verdicts"] = [{"violations": violations, "verdict": "fail"}]
        result, _attempt, thread = self._invoke(stage, context, run_id=run_id, entity=entity, revision=revision)
        action = str(result["action"])
        if action == "accept":
            return "quarantine", thread
        return action, thread


    def _validate_candidate(self, run_id: str, entity: str, attempt_id: str, source: str, candidate: str) -> tuple[ValidationEvidence, Path]:
        evidence = validate(source, candidate, self.definition.validation)
        path = self._write_artifact("evidence", entity, f"{attempt_id}.validation.json", json.dumps(evidence.as_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        self.store.record_validation(run_id, entity, attempt_id, evidence.passed, evidence.as_dict(), str(path))
        return evidence, path


    def _invoke_analysis(self, stage: PromptStage, context: Mapping[str, Any], run_id: str, subject: str) -> tuple[Mapping[str, Any], str]:
        if self.client is None:
            raise StateError("analysis requires configured local inference")
        prompt = self.prompts[stage.name]
        inputs = {name: context[name] for name in prompt.inputs if name in context}
        rendered = prompt.render(inputs)
        attempt_id = f"a-{uuid.uuid4().hex[:16]}"
        response = self.client.invoke(
            InferenceRequest(
                messages=[{"role": "user", "content": rendered}],
                response_format=self.schemas.schema_for(prompt.output),
                stage=f"analysis-{stage.name}",
                run_id=run_id,
                entity_id=subject,
                entity_revision="post-run",
                attempt_id=attempt_id,
                prompt_template_id=prompt.prompt_id,
                prompt_template_hash=prompt.content_hash,
            )
        )
        return self.schemas.validate(prompt.output, response.content), str(response.capture_path) if response.capture_path else ""


    def _repair(
        self,
        source: str,
        candidate: str,
        violations: list[Any],
        *,
        run_id: str,
        entity: str,
        revision: str,
    ) -> tuple[str | None, str, str]:
        stage = self.definition.stages.get("repair")
        if stage is None or self.definition.runtime.max_repairs < 1:
            return None, "", ""
        result, attempt, thread = self._invoke(stage, self._context(source, candidate, violations=violations), run_id=run_id, entity=entity, revision=revision)
        if result["status"] != "repaired" or result.get("unresolved") or not isinstance(result.get("candidate"), str):
            return None, attempt, thread
        return str(result["candidate"]), attempt, thread


    def _semantic_review(self, source: str, candidate: str, evidence: ValidationEvidence, *, run_id: str, entity: str, revision: str) -> tuple[bool, list[Any], str]:
        threads: list[str] = []
        for name in ("self_review", "reviewer"):
            stage = self.definition.stages.get(name)
            if stage is None:
                continue
            result, _attempt, thread = self._invoke(stage, self._context(source, candidate, evidence.as_dict()), run_id=run_id, entity=entity, revision=revision)
            if thread:
                threads.append(thread)
            if result["verdict"] != "pass" or result.get("violations"):
                return False, list(result.get("violations", [])), threads[-1] if threads else ""
        return True, [], threads[-1] if threads else ""
