"""Stable public evidence interface composed from focused evidence modules.
Re-export rejected-artifact persistence and run-report rendering contracts.
Implementations document their filesystem effects in the component modules.
"""

from .rejection_evidence import (
    GOVERNANCE_VERSION,
    _safe_component,
    classify_failure,
    rejection_explanation,
    rejection_record,
    rejected_candidate_path,
    rejected_sequence,
    rejected_content_extension,
    is_non_progress,
    rejection_explanation_path,
    diagnostic_render_path,
    diagnostic_render_explanation_path,
    _atomic_create,
    persist_rejected_pair,
    persist_diagnostic_render_pair,
    persist_sequential_rejected_pair,
    persist_rejection_bundle,
)

from .run_evidence import (
    execution_status,
    build_run_evidence,
    _cell,
    render_run_markdown,
)
