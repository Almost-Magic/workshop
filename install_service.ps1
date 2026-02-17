# The Workshop — nssm Service Registration
# Run as Administrator on Windows.
#
# Registers The Workshop Flask API as a Windows service
# via nssm 2.24. The service starts automatically at boot
# and restarts on failure.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install_service.ps1

$ErrorActionPreference = "Stop"

# ── Paths ──────────────────────────────────────────────────────────────────
$nssm = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe\nssm-2.24-101-g897c7ad\win64\nssm.exe"
$python = "python"
$workshopDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appScript = Join-Path $workshopDir "app.py"
$logDir = Join-Path $workshopDir "logs"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# ── Remove existing service if present ─────────────────────────────────────
Write-Host "Checking for existing AMTL-Workshop service..."
$existing = & $nssm status AMTL-Workshop 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Stopping and removing existing service..."
    & $nssm stop AMTL-Workshop 2>&1 | Out-Null
    & $nssm remove AMTL-Workshop confirm
}

# ── Install Workshop API service ───────────────────────────────────────────
Write-Host "Installing AMTL-Workshop service..."
& $nssm install AMTL-Workshop $python $appScript
& $nssm set AMTL-Workshop AppDirectory $workshopDir
& $nssm set AMTL-Workshop DisplayName "AMTL Workshop API"
& $nssm set AMTL-Workshop Description "The Workshop — AMTL Central Service Registry & Launcher (port 5003)"
& $nssm set AMTL-Workshop Start SERVICE_AUTO_START
& $nssm set AMTL-Workshop AppStdout (Join-Path $logDir "workshop.log")
& $nssm set AMTL-Workshop AppStderr (Join-Path $logDir "workshop-error.log")
& $nssm set AMTL-Workshop AppRotateFiles 1
& $nssm set AMTL-Workshop AppRotateBytes 5242880

Write-Host "Starting AMTL-Workshop service..."
& $nssm start AMTL-Workshop

Write-Host ""
Write-Host "AMTL-Workshop service installed and started." -ForegroundColor Green
Write-Host "Verify: curl http://localhost:5003/api/health"

# ── Install Watchdog service ───────────────────────────────────────────────
$watchdogScript = Join-Path $workshopDir "watchdog.py"

Write-Host ""
Write-Host "Checking for existing AMTL-Watchdog service..."
$existing = & $nssm status AMTL-Watchdog 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Stopping and removing existing watchdog..."
    & $nssm stop AMTL-Watchdog 2>&1 | Out-Null
    & $nssm remove AMTL-Watchdog confirm
}

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

Write-Host ""
Write-Host "Both services installed and running." -ForegroundColor Green
Write-Host "  AMTL-Workshop  → http://localhost:5003/api/health"
Write-Host "  AMTL-Watchdog  → monitoring Workshop + Supervisor every 30s"
