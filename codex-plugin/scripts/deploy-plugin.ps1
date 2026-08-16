param(
    [string]$Target = "$env:USERPROFILE\plugins\ppt-workflow-studio"
)

$source = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $Target)) {
    throw "Plugin target does not exist: $Target"
}

Copy-Item -LiteralPath (Join-Path $source '.codex-plugin') -Destination $Target -Recurse -Force
Copy-Item -LiteralPath (Join-Path $source 'skills') -Destination $Target -Recurse -Force
