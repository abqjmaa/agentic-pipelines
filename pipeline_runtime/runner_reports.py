"""Structured run reports, human narratives and advisory cohort analysis.
Composes with PipelineRunner through its definition, store and stage interfaces.
May persist artifacts or call configured inference only through runner contracts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .evidence import build_run_evidence, render_run_markdown
from .state import StateError

from .runner_io import _atomic_write


class RunnerReportsMixin:
    def inspect(self, entity: str) -> dict[str, Any] | None:
        return self.store.entity(entity)


    def report(self, run_id: str | None = None, *, learning_status: str | None = None) -> Path:
        self.definition.report_root.mkdir(parents=True, exist_ok=True)
        performance = self.store.run_metrics(run_id)
        actual_run_id = performance.get("run_id")
        if not actual_run_id:
            data = {
                "schema_version": 5,
                "governance_version": "deterministic-semantic-human-v2",
                "pipeline_id": self.definition.pipeline_id,
                "run_id": run_id or "current-summary",
                "execution_status": "no_op",
                "learning_status": "not_required",
                "started_at": None,
                "finished_at": None,
                "checkpointed_at": None,
                "reconciled": False,
                "summary": {"state": self.store.summary(), "run": {}, "failure_cohorts": self.store.failure_cohorts()},
                "state": self.store.summary(),
                "performance": performance,
                "failure_cohorts": self.store.failure_cohorts(),
                "attempts": [],
                "rejected_artifacts": [],
                "observations": ["No recorded run exists; this is a deterministic current-state summary."],
                "metrics": performance,
                "hypotheses": [],
                "recommendations": [],
            }
            path = self.definition.report_root / "current-summary.json"
        else:
            data = build_run_evidence(
                pipeline_id=self.definition.pipeline_id,
                run_evidence=self.store.run_evidence(str(actual_run_id)),
                state_summary=self.store.summary(),
                performance=performance,
                failure_cohorts=self.store.failure_cohorts(),
            )
            if learning_status is not None:
                data["learning_status"] = learning_status
            path = self.definition.report_root / f"{actual_run_id}.json"
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "run_evidence.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda error: list(error.path))
        if errors:
            location = ".".join(str(part) for part in errors[0].path) or "$"
            raise StateError(f"run evidence failed at {location}: {errors[0].message}")
        _atomic_write(path, (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
        narrative = path.with_suffix(".md")
        _atomic_write(narrative, render_run_markdown(data, path).encode("utf-8"))
        return path


    def analyze(self, run_id: str | None = None) -> Path:
        deterministic_path = self.report(run_id)
        deterministic = json.loads(deterministic_path.read_text(encoding="utf-8"))
        actual_run_id = deterministic["performance"].get("run_id") or run_id or "run-analysis"
        output: dict[str, Any] = {
            "schema_version": 1,
            "authority": "advisory_only",
            "deterministic_report": str(deterministic_path),
            "observations": deterministic,
            "cohort_analyses": [],
            "performance_analysis": None,
        }
        failure_stage = self.definition.analysis.get("failure")
        remediation_stage = self.definition.analysis.get("remediation")
        if failure_stage:
            for cohort in deterministic["failure_cohorts"]:
                representatives = []
                for entity in cohort["entity_ids"][:3]:
                    evidence = self.store.entity(entity)
                    if evidence:
                        representatives.append({"entity_id": entity, "state": evidence["entity"]["state"], "error_code": evidence["entity"]["error_code"], "transitions": [{"to_state": item["to_state"], "reason": item["reason"]} for item in evidence["transitions"]]})
                analysis, thread = self._invoke_analysis(
                    failure_stage,
                    {"cohort_definition": cohort, "representative_evidence": representatives, "run_context": deterministic["performance"]},
                    str(actual_run_id),
                    cohort["cohort_id"],
                )
                item: dict[str, Any] = {"cohort": cohort, "analysis": analysis, "thread": thread}
                if remediation_stage:
                    proposal, proposal_thread = self._invoke_analysis(
                        remediation_stage,
                        {"reviewed_cohort_analysis": analysis, "pipeline_contract": {"goal": self.definition.goal, "allowed_changes": self.definition.allowed_changes, "protected_invariants": self.definition.protected_invariants}},
                        str(actual_run_id),
                        cohort["cohort_id"],
                    )
                    item["remediation_proposal"] = proposal
                    item["remediation_thread"] = proposal_thread
                output["cohort_analyses"].append(item)
        performance_stage = self.definition.analysis.get("performance")
        if performance_stage:
            analysis, thread = self._invoke_analysis(
                performance_stage,
                {
                    "deterministic_run_metrics": deterministic["performance"],
                    "execution_trajectory": deterministic.get("attempts", []),
                    "evaluation_metrics": {"false_accept_rate": "unknown", "false_reject_rate": "unknown"},
                },
                str(actual_run_id),
                "performance",
            )
            output["performance_analysis"] = {"analysis": analysis, "thread": thread}
        path = self.definition.report_root / f"{actual_run_id}.post-run.json"
        _atomic_write(path, (json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
        if deterministic.get("run_id"):
            self.report(str(deterministic["run_id"]), learning_status="completed")
        return path
