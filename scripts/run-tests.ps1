param(
    [string]$Python
)

$ErrorActionPreference = 'Stop'
$collectionRoot = Split-Path -Parent $PSScriptRoot
$bootstrap = Join-Path $collectionRoot 'ppt-workflow\scripts\bootstrap.ps1'

if (-not (Test-Path -LiteralPath $bootstrap -PathType Leaf)) {
    Write-Error "Cannot find dependency bootstrap at $bootstrap"
    exit 1
}

$powerShellCommand = Get-Command pwsh -ErrorAction SilentlyContinue
if ($null -eq $powerShellCommand) {
    $powerShellCommand = Get-Command powershell -ErrorAction SilentlyContinue
}
if ($null -eq $powerShellCommand) {
    Write-Error 'No PowerShell executable found to run the dependency bootstrap.'
    exit 1
}

$bootstrapArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $bootstrap)
if (-not [string]::IsNullOrWhiteSpace($Python)) {
    $bootstrapArgs += @('-Python', $Python)
}

Push-Location $collectionRoot
try {
    & $powerShellCommand.Source @bootstrapArgs
    $bootstrapExitCode = $LASTEXITCODE
    if ($bootstrapExitCode -ne 0) {
        Write-Error "Dependency preflight failed; tests were not started (exit code $bootstrapExitCode)."
        exit $bootstrapExitCode
    }

    if ([string]::IsNullOrWhiteSpace($Python)) {
        $venvPython = Join-Path $collectionRoot '.venv\Scripts\python.exe'
        if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
            $Python = $venvPython
        } else {
            $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
            if ($null -eq $pythonCommand) {
                $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
                if ($null -eq $pythonCommand) {
                    Write-Error 'The Python interpreter resolved by bootstrap is no longer available.'
                    exit 1
                }
            }
            $Python = $pythonCommand.Source
        }
    }

    $testCommands = @(
        @('ppt-workflow/tests', 'test_*.py'),
        @('html-to-pptx/tests', 'test_*.py')
    )
    foreach ($testCommand in $testCommands) {
        $testRoot = $testCommand[0]
        $pattern = $testCommand[1]
        Write-Host "Running unittest discovery: $testRoot"
        & $Python -m unittest discover -s $testRoot -p $pattern -v
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    exit 0
} finally {
    Pop-Location
}
