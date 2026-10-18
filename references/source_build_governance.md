# Source and build governance

This is the canonical source-code and build-pipeline policy. It applies to all
first-party implementation, tooling, examples, and tests, including this framework.
Updating a submodule pointer does not by itself migrate a host's source or builds.

## Source organization

Declare every source root in `api.yaml` under `code.roots`. Roots are repository-root
directories such as `src`, `scripts`, `tests`, or `pipeline_runtime`, not `.` or
individual files. All first-party source must be inside a declared root. Nested
directories are allowed. Tests, examples, launchers, and generated first-party
source are not blanket exceptions. Git submodules are separately governed repos;
ignored dependency installations and build products are not first-party source.

Every directory in each source root must contain `README.md`, briefly describing
its purpose and every directly contained source file. Use the exact backticked
filename followed by a nonempty description (`- `filename.py`: responsibility`).
Keep inventories current when adding, moving, deleting, or decomposing files.

Every source file must start with a language-appropriate multiline explanatory
comment (a module docstring in Python). Explain responsibilities, interfaces,
dependencies, and side effects. A language without block comments uses contiguous
line comments. A shebang, encoding declaration, or mandatory language directive
may precede the header. Presence is checked mechanically; correctness and coverage
are review responsibilities. Do not generate meaningless filler to satisfy the gate.

## Size and composition

Each source file has a maximum of **400 counted physical lines**: 400 passes and
401 fails. Blank lines and recognized comment-only lines, including multiline
comments, do not count. A code line with an inline comment counts. Continuation
lines count. Executable multiline strings (SQL, templates, fixtures) count;
delimiters inside strings cannot turn code into comments. Python true docstrings
are comments for this accounting, not arbitrary triple-quoted strings.

Decompose over-limit files by responsibility and compose explicit interfaces.
Preserve behavior and service/process boundaries. Do not use dynamic source
loading, compressed lines, generated wrappers, or miscellaneous chunks to evade
the limit. Each new component must have a coherent name, header, and README entry.

## One action per line

Use one logical statement per line. No semicolon-separated actions, chained
assignments, assignment expressions, or assignments embedded in comparisons or
conditions. Put a branch/loop header and its body on separate lines. Ordinary
assignment of a function's result and tuple unpacking are single statements.
For-loop grammar separators are not separate actions. Avoid nested side effects
and expressions that hide multiple responsibilities even when syntactically legal.
Language-specific checks establish syntax properties only; review establishes
whether a statement is appropriately simple. Unsupported language adapters must
fail explicitly, never silently certify source they cannot parse.

## Configuration and canonical check

Track the public `code` mapping in `api.sample.yaml`; copy the same mapping into
ignored local `api.yaml`. The checker uses the tracked mapping in CI and compares
an existing local mapping against it. A missing or different local mapping fails;
it must not weaken policy. It never reads or prints endpoint credentials and
needs no model service. Configure `comment_pattern` for each extension/adapter.
Only parser-recognized comments matching that pattern are excluded. A pattern
that matches ordinary code cannot remove code lines from the count.

Run `python agentic-pipelines/scripts/check_source_governance.py --repo-root .`
from a host; omit the submodule prefix within the framework. The recursive check
reports every failure and exits nonzero. Use `--staged` for the Git index. Staged
checks read staged data using the trusted installed checker; they never execute
staged scripts or materialize staged symlinks. Fix violations; do not add a bypass.

## Mandatory commit and build gates

**Every build pipeline must include this check and fail the build when it fails.**
This includes local build scripts, CI, release/package/container jobs, alternate
platforms, and scheduled/manual builds. Run the gate before compilation, bundling,
rendering, packaging, or publication. Do not ignore its exit status, use
`continue-on-error`, wrap it in an advisory condition, or run it concurrently with
the build it protects. Recheck after source generation and before compiling that
generated source. Dependency installation needed to run the checker may precede it.

Use `scripts/governed_build.py --repo-root . -- COMMAND ARG...` as the reusable
fail-closed wrapper for arbitrary build commands. Existing build scripts must call
the checker or this wrapper and propagate failure. Register each pipeline in
`code.build_pipelines`; GitHub Actions paths are also discovered so an omitted
workflow cannot escape inspection. Each executable Actions job must contain the
canonical named gate step before build/test commands. The checker validates the
supported Actions wiring, not arbitrary shell semantics. Other build systems need
an integration regression proving a failing source gate prevents their command.

Install the framework pre-commit integration with
`python agentic-pipelines/scripts/install_source_governance_hook.py --repo-root .`.
It checks the staged snapshot and chains existing hooks without overwriting them.
Host bootstrap must install/check this integration. CI must run the committed-tree
check and tests on every PR/push, with the governance job selected as a required
branch check. Local hooks and direct compiler calls are bypassable; required remote
checks and governed entrypoints provide enforcement, not a claim to intercept all
possible Git/compiler invocations. Changing remote protection requires repository
administration authority and must be reported separately from checked-in wiring.

Adoption includes source decomposition, documentation, configuration, hook setup,
every build integration, regression tests, and a passing gate. Prepare that complete
tree before enabling enforcement. Record exact remaining host work; do not claim
compliance merely from documentation or a newer framework pointer.
