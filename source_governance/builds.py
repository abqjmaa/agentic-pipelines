"""
Audit registered build gates and discover GitHub Actions jobs independently.
Require a blocking source-check step before build/test commands in every job.
Static wiring checks supplement failure-injection tests, not shell interpretation.
"""

import re
import yaml


GATE = re.compile(
    r"^python(?:3)? (?:[A-Za-z0-9_-]+/)?scripts/check_source_governance\.py --repo-root \.$"
)


def inspect_builds(snapshot, config):
    issues = []
    registered = {}
    for item in config["build_pipelines"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            issues.append("build_pipelines entries need path and kind")
            continue
        path = item["path"]
        registered[path] = item.get("kind")
        if path not in snapshot.files:
            issues.append(f"{path}: registered build pipeline is missing")
    workflows = {
        name for name in snapshot.files
        if name.startswith(".github/workflows/") and name.endswith((".yml", ".yaml"))
    }
    conventional = {
        name for name in snapshot.files
        if name.rsplit("/", 1)[-1] in {"Makefile", "Dockerfile", "Jenkinsfile", "azure-pipelines.yml", ".gitlab-ci.yml"}
    }
    for path in sorted(conventional - set(registered)):
        issues.append(f"{path}: build pipeline is not registered in code.build_pipelines")
    for path in sorted(workflows | set(registered)):
        if path not in registered:
            issues.append(f"{path}: build pipeline is not registered in code.build_pipelines")
        if path in workflows:
            issues.extend(inspect_actions(snapshot, path))
        elif registered.get(path) != "governed-wrapper":
            issues.append(f"{path}: unsupported build integration; use governed-wrapper")
        elif path in snapshot.files:
            text = snapshot.read(path)
            if "governed_build.py" not in text:
                issues.append(f"{path}: missing canonical governed_build.py invocation")
    return issues


def inspect_actions(snapshot, path):
    data = yaml.safe_load(snapshot.read(path))
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), dict):
        return [f"{path}: missing Actions jobs"]
    issues = []
    if data.get("defaults"):
        issues.append(f"{path}: workflow run defaults require a dedicated audited gate adapter")
    for name, job in data["jobs"].items():
        prefix = f"{path}:{name}"
        if not isinstance(job, dict):
            issues.append(f"{prefix}: invalid job")
            continue
        if job.get("continue-on-error"):
            issues.append(f"{prefix}: build job cannot ignore failures")
        if job.get("defaults"):
            issues.append(f"{prefix}: job run defaults require a dedicated audited gate adapter")
        steps = job.get("steps", [])
        gated = False
        for step in steps:
            if not isinstance(step, dict):
                issues.append(f"{prefix}: invalid step")
                continue
            if step.get("name") == "Source governance":
                run = str(step.get("run", "")).strip()
                if not GATE.fullmatch(run) or set(step) != {"name", "run"}:
                    issues.append(f"{prefix}: source gate must be unconditional and propagate failure")
                else:
                    gated = True
                continue
            if gated:
                continue
            run = str(step.get("run", "")).strip()
            # Only checker dependency installation can run before governance.
            if run and not re.fullmatch(r"python -m pip install (?:PyYAML|\-r requirements\.txt)", run):
                issues.append(f"{prefix}: command precedes source gate")
            uses = str(step.get("uses", ""))
            if uses and not uses.startswith(("actions/checkout@", "actions/setup-python@")):
                issues.append(f"{prefix}: action precedes source gate")
        if not gated:
            issues.append(f"{prefix}: missing Source governance gate")
    return issues
