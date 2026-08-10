param(
    [string]$WorkspaceRoot = (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
)

$ErrorActionPreference = 'Stop'
$collectionRoot = Join-Path $WorkspaceRoot 'ppt-skills-collection'
$requirements = Join-Path $collectionRoot 'html-to-pptx\requirements.txt'
$venv = Join-Path $WorkspaceRoot '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $requirements)) {
    throw "Cannot find requirements at $requirements. Pass the workspace root containing ppt-skills-collection."
}
if (-not (Test-Path -LiteralPath $python)) {
    & py -3 -m venv $venv
}

& $python -m pip install --upgrade pip
& $python -m pip install -r $requirements
& $python -m playwright install chromium
& $python -c "import sys; sys.path.insert(0, r'$collectionRoot\html-to-pptx\scripts'); from playwright.sync_api import sync_playwright; from browser_runtime import launch_browser; p=sync_playwright().start(); b,name=launch_browser(p); page=b.new_page(); page.set_content('<main>ok</main>'); assert page.locator('main').inner_text() == 'ok'; b.close(); p.stop(); print(f'PPT runtime health check passed ({name})')"
