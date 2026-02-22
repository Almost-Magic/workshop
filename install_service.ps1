# The Workshop — nssm Service Registration
# Run as Administrator on Windows.
#
# Registers The Workshop Flask API and Meta-Watchdog as Windows services
# via nssm 2.24. Both services start automatically at boot
# and restart on failure.
#
# Usage (paste into Cline or run as Admin in PowerShell):
#   powershell -ExecutionPolicy Bypass -File install_service.ps1
#
# Ref: AMTL-WKS-BLD-1.0 Phase 0, DEC-004

$ErrorActionPreference = "Stop"

# ── Find nssm ────────────────────────────────────────────────────────────────
# Check PATH first, then common locations, then winget package path
$nssm = $null
$nssmCandidates = @(
    (Get-Command nssm -ErrorAction SilentlyContinue).Source,
    "C:\tools\nssm\win64\nssm.exe",
    "C:\nssm\win64\nssm.exe",
    "$env:ProgramFiles\nssm\win64\nssm.exe",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe\nssm-2.24-101-g897c7ad\win64\nssm.exe"
)

foreach ($candidate in $nssmCandidates) {
    if ($candidate -and (Test-Path $candidate)) {
        $nssm = $candidate
        break
    }
}

if (-not $nssm) {
    Write-Host "nssm not found. Installing via winget..." -ForegroundColor Yellow
    winget install NSSM.NSSM --accept-package-agreements --accept-source-agreements
    # Try to find it after install
    $nssm = (Get-Command nssm -ErrorAction SilentlyContinue).Source
    if (-not $nssm) {
        Write-Host "ERROR: nssm still not found after install. Please install manually from https://nssm.cc/download" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Using nssm at: $nssm" -ForegroundColor Cyan

# ── Find Python ───────────────────────────────────────────────────────────────
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Write-Host "ERROR: Python not found on PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Using Python at: $python" -ForegroundColor Cyan

# ── Paths ─────────────────────────────────────────────────────────────────────
$workshopDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appScript = Join-Path $workshopDir "app.py"
$logDir = Join-Path $workshopDir "logs"

Write-Host "Workshop directory: $workshopDir" -ForegroundColor Cyan

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# ── Remove existing Workshop service if present ──────────────────────────────
Write-Host "`nChecking for existing AMTL-Workshop service..."
$existing = & $nssm status AMTL-Workshop 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Stopping and removing existing service..."
    & $nssm stop AMTL-Workshop 2>&1 | Out-Null
    & $nssm remove AMTL-Workshop confirm
}

# ── Install Workshop API service ─────────────────────────────────────────────
Write-Host "Installing AMTL-Workshop service..."
& $nssm install AMTL-Workshop $python $appScript
& $nssm set AMTL-Workshop AppDirectory $workshopDir
& $nssm set AMTL-Workshop DisplayName "AMTL Workshop API"
& $nssm set AMTL-Workshop Description "AMTL Central Service Registry and Launcher on port 5003"
& $nssm set AMTL-Workshop Start SERVICE_AUTO_START
& $nssm set AMTL-Workshop AppStdout (Join-Path $logDir "workshop.log")
& $nssm set AMTL-Workshop AppStderr (Join-Path $logDir "workshop-error.log")
& $nssm set AMTL-Workshop AppRotateFiles 1
& $nssm set AMTL-Workshop AppRotateBytes 5242880

Write-Host "Starting AMTL-Workshop service..."
& $nssm start AMTL-Workshop

Write-Host "`nAMTL-Workshop service installed and started." -ForegroundColor Green
Write-Host "Verify: curl http://localhost:5003/api/health"

# ── Remove existing Watchdog service if present ──────────────────────────────
$watchdogScript = Join-Path $workshopDir "watchdog.py"

Write-Host "`nChecking for existing AMTL-Watchdog service..."
$existing = & $nssm status AMTL-Watchdog 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Stopping and removing existing watchdog..."
    & $nssm stop AMTL-Watchdog 2>&1 | Out-Null
    & $nssm remove AMTL-Watchdog confirm
}

# ── Install Watchdog service ─────────────────────────────────────────────────
Write-Host "Installing AMTL-Watchdog service..."
& $nssm install AMTL-Watchdog $python $watchdogScript
& $nssm set AMTL-Watchdog AppDirectory $workshopDir
& $nssm set AMTL-Watchdog DisplayName "AMTL Meta-Watchdog"
& $nssm set AMTL-Watchdog Description "Checks Workshop and Supervisor health every 30 seconds, restarts if down"
& $nssm set AMTL-Watchdog Start SERVICE_AUTO_START
& $nssm set AMTL-Watchdog AppStdout (Join-Path $logDir "watchdog.log")
& $nssm set AMTL-Watchdog AppStderr (Join-Path $logDir "watchdog-error.log")

Write-Host "Starting AMTL-Watchdog service..."
& $nssm start AMTL-Watchdog

Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "Both services installed and running." -ForegroundColor Green
Write-Host "  AMTL-Workshop  → http://localhost:5003/api/health" -ForegroundColor Green
Write-Host "  AMTL-Watchdog  → monitoring Workshop + Supervisor every 30s" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
