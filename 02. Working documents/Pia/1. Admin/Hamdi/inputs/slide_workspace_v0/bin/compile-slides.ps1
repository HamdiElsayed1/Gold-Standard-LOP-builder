# Wrapper that invokes html_to_pptx.py through the project venv,
# with the bundled template as the default.

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Script = "$ProjectRoot\scripts\html_to_pptx.py"
$DefaultTpl = "$ProjectRoot\pptx-template.pptx"

$Python = "$ProjectRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$NeedsTemplate = $true
foreach ($a in $args) {
    if ($a -eq "-t" -or $a -eq "--template") { $NeedsTemplate = $false; break }
}

if ($NeedsTemplate) {
    & $Python $Script @args -t $DefaultTpl
} else {
    & $Python $Script @args
}
exit $LASTEXITCODE
