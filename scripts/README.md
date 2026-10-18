# scripts

This directory owns scripts assets.

## Source inventory

- `bootstrap_pipeline_environment.py`: Install declared pipeline dependencies into an ignored host-local directory.
- `check_source_governance.py`: Run the canonical source/build check against a repository or its Git index.
- `ensure_ollama_context_aliases.py`: Ensure selected context aliases exist in a local Docker-hosted Ollama.
- `governed_build.py`: Gate an arbitrary build command with the canonical source governance check.
- `install_source_governance_hook.py`: Install or check a staged source gate while preserving an existing pre-commit hook.
- `lint_prompts.py`: Validate prompt identity, metadata, contracts, and narrow authority.
- `pipeline.py`: Operate a bounded local Pipelines runtime from a host repository.
- `regenerate_plan_indexes.py`: Validate plan files and regenerate per-status plan indexes.
- `render_markdown_pdf.py`: Render a Markdown file to a sibling PDF using a local, self-bootstrapped environment.
- `validate_pipeline_package.py`: Validate a staged package without configuring inference or starting work.
