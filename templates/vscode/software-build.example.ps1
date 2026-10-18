<#
Bootstrap declared host prerequisites, then gate the host software build.
Adapt into a declared host scripts root and replace command markers from its environment.
Both VS Code task and launch entrypoints use this same failing build path.
#>
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$BuildArgs)

$ErrorActionPreference = 'Stop'

try {
    if (-not (Get-Command REPLACE_PYTHON_COMMAND -ErrorAction SilentlyContinue)) {
        throw 'build: host Python is unavailable'
    }
    & REPLACE_PYTHON_COMMAND -B "$PSScriptRoot/bootstrap.py"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    & REPLACE_PYTHON_COMMAND -B "$PSScriptRoot/../agentic-pipelines/scripts/governed_build.py" --repo-root "$PSScriptRoot/.." -- REPLACE_BUILD_COMMAND @BuildArgs
    exit $LASTEXITCODE
}
catch [System.Management.Automation.PipelineStoppedException] {
    Write-Error 'build: interrupted'
    exit 130
}
catch {
    Write-Error "build: $($_.Exception.Message)"
    exit 1
}
