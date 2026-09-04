param(
    [switch]$Install,
    [string]$Python
)

$ErrorActionPreference = 'Stop'

$collectionRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$dependencyMap = [ordered]@{
    pypdf      = 'pypdf'
    openpyxl   = 'openpyxl'
    defusedxml = 'defusedxml'
    pptx       = 'python-pptx'
    lxml       = 'lxml'
    fontTools  = 'fonttools'
    playwright = 'playwright'
    PIL        = 'Pillow'
    pdf2image  = 'pdf2image'
}

# pywin32 is only declared on Windows, where PowerPoint COM and native video
# embedding are available.
if ($env:OS -eq 'Windows_NT') {
    $dependencyMap['win32com.client'] = 'pywin32'
}

function Resolve-Python {
    param([string]$Requested)

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (Test-Path -LiteralPath $Requested -PathType Leaf) {
            return (Resolve-Path -LiteralPath $Requested).Path
        }
        $command = Get-Command $Requested -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
        throw "Python executable not found: $Requested"
    }

    $venvPython = Join-Path $collectionRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        return $venvPython
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        return $pythonCommand.Source
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyCommand) {
        return $pyCommand.Source
    }

    throw 'No Python interpreter found. Install Python 3.10+ or pass -Python <path>.'
}

function Test-PythonImport {
    param(
        [string]$Interpreter,
        [string]$ImportName
    )

    $probe = "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('$ImportName') else 1)"
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $Interpreter -c $probe 2>$null
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    return $exitCode -eq 0
}

function Resolve-FFmpeg {
    $configured = $env:PPT_FFMPEG_EXECUTABLE
    if (-not [string]::IsNullOrWhiteSpace($configured)) {
        if (Test-Path -LiteralPath $configured -PathType Leaf) {
            return (Resolve-Path -LiteralPath $configured).Path
        }
        Write-Warning "PPT_FFMPEG_EXECUTABLE does not point to a file: $configured. Falling back to PATH."
    }

    $command = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    return $null
}

function Test-FFmpegWithLibx264 {
    param([string]$Executable)

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Executable -version *> $null
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        $encoders = & $Executable -hide_banner -encoders 2>$null
        return $LASTEXITCODE -eq 0 -and $encoders -match '\blibx264\b'
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

try {
    $pythonPath = Resolve-Python -Requested $Python
    Write-Host "Python: $pythonPath"

    $workflowRequirements = Join-Path $collectionRoot 'ppt-workflow\requirements.txt'
    $converterRequirements = Join-Path $collectionRoot 'html-to-pptx\requirements.txt'
    if (-not (Test-Path -LiteralPath $workflowRequirements -PathType Leaf)) {
        throw "Cannot find requirements at $workflowRequirements"
    }
    if (-not (Test-Path -LiteralPath $converterRequirements -PathType Leaf)) {
        throw "Cannot find requirements at $converterRequirements"
    }

    if ($Install) {
        Write-Host 'Installing workflow and converter requirements...'
        & $pythonPath -m pip install -r $workflowRequirements -r $converterRequirements
        if ($LASTEXITCODE -ne 0) {
            throw "Dependency installation failed with exit code $LASTEXITCODE"
        }

        Write-Host 'Installing Playwright Chromium browser...'
        & $pythonPath -m playwright install chromium
        if ($LASTEXITCODE -ne 0) {
            throw "Playwright browser installation failed with exit code $LASTEXITCODE"
        }
    }

    $missing = [System.Collections.Generic.List[string]]::new()
    foreach ($importName in $dependencyMap.Keys) {
        if (Test-PythonImport -Interpreter $pythonPath -ImportName $importName) {
            Write-Host "[PASS] $importName ($($dependencyMap[$importName]))"
        } else {
            Write-Host "[MISSING] $importName ($($dependencyMap[$importName]))"
            $missing.Add($dependencyMap[$importName])
        }
    }

    if ($missing.Count -gt 0) {
        $uniqueMissing = @($missing | Select-Object -Unique)
        Write-Output ("Missing Python packages: {0}" -f ($uniqueMissing -join ', '))
        $quotedPython = '"' + $pythonPath + '"'
        Write-Output ("Install them with: {0} -m pip install -r ppt-workflow/requirements.txt -r html-to-pptx/requirements.txt" -f $quotedPython)
        exit 1
    }

    $ffmpegPath = Resolve-FFmpeg
    if ($null -eq $ffmpegPath) {
        Write-Warning 'FFmpeg not found. Video-motion integration tests and native video embedding will be skipped; install FFmpeg or set PPT_FFMPEG_EXECUTABLE.'
    } elseif (Test-FFmpegWithLibx264 -Executable $ffmpegPath) {
        Write-Host "[PASS] ffmpeg with libx264 ($ffmpegPath)"
    } else {
        Write-Warning "FFmpeg is unavailable or lacks libx264: $ffmpegPath. Video-motion integration tests and native video embedding will be skipped."
    }

    Write-Host 'All required Python imports are available.'
    exit 0
} catch {
    Write-Error $_
    exit 1
}
