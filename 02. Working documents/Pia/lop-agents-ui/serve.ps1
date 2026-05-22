# Serves the agents dashboard at http://127.0.0.1:3000/ — Python only (no Node).
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$static = Join-Path $here "static"
if (-not (Test-Path -LiteralPath $static)) {
    Write-Host "Missing folder: $static" -ForegroundColor Red
    exit 1
}

$py = $null
foreach ($name in @("py", "python", "python3")) {
    $c = Get-Command $name -ErrorAction SilentlyContinue
    if ($c) { $py = $c.Name; break }
}
if (-not $py) {
    Write-Host "Python not found. Install Python 3 from https://www.python.org/ (add to PATH)." -ForegroundColor Yellow
    exit 1
}

Write-Host "LoP agents dashboard → http://127.0.0.1:3000/" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Set-Location $here
# Python 3.7+: --directory serves files from ./static so / maps to index.html
& $py -m http.server 3000 --bind 127.0.0.1 --directory static
