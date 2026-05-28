<#
.SYNOPSIS
    Idempotently registers, updates, or removes the LaunchLook audit-queue
    scheduled task in Windows Task Scheduler.

.DESCRIPTION
    Wraps schtasks.exe so you never have to hand-write the command again.
    Safe to run multiple times: deletes and re-creates if the task already
    exists, so config changes always take effect.

.PARAMETER Action
    install  - Register (or update) the task. Default.
    remove   - Delete the task.
    status   - Print current task state without modifying anything.

.PARAMETER Interval
    How often the task fires, in minutes. Default: 30.

.PARAMETER Provider
    LLM provider to pass to process_audit_queue.py. Default: gpt.

.PARAMETER Limit
    Max jobs per run. Default: 3.

.EXAMPLE
    # Register the task (runs every 30 min, up to 3 jobs)
    .\scripts\install_scheduler.ps1

    # Change interval to 60 min
    .\scripts\install_scheduler.ps1 -Interval 60

    # Remove the task entirely
    .\scripts\install_scheduler.ps1 -Action remove

    # Check current state
    .\scripts\install_scheduler.ps1 -Action status
#>

[CmdletBinding()]
param(
    [ValidateSet('install','remove','status')]
    [string]$Action   = 'install',
    [int]   $Interval = 30,
    [string]$Provider = 'gpt',
    [int]   $Limit    = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TaskName   = 'LaunchLook Audit Queue'
$RepoRoot   = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PythonExe  = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $PythonExe) { $PythonExe = 'python' }

$ScriptPath = Join-Path $RepoRoot 'scripts\process_audit_queue.py'
$LogDir     = Join-Path $RepoRoot 'logs'
$LogFile    = Join-Path $LogDir   'scheduler.log'

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
function Get-TaskExists {
    $result = schtasks /query /tn $TaskName 2>&1
    return ($LASTEXITCODE -eq 0)
}

# ------------------------------------------------------------------
# status
# ------------------------------------------------------------------
if ($Action -eq 'status') {
    if (Get-TaskExists) {
        Write-Host "[scheduler] Task '$TaskName' is registered."
        schtasks /query /tn $TaskName /fo LIST /v 2>&1 |
            Where-Object { $_ -match 'Status|Next Run|Last Run|Last Result|Task To Run' } |
            ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Host "[scheduler] Task '$TaskName' is NOT registered."
    }
    exit 0
}

# ------------------------------------------------------------------
# remove
# ------------------------------------------------------------------
if ($Action -eq 'remove') {
    if (Get-TaskExists) {
        schtasks /delete /tn $TaskName /f | Out-Null
        Write-Host "[scheduler] Task '$TaskName' removed."
    } else {
        Write-Host "[scheduler] Task '$TaskName' was not registered; nothing to remove."
    }
    exit 0
}

# ------------------------------------------------------------------
# install (idempotent: delete first if exists, then create)
# ------------------------------------------------------------------
if (Get-TaskExists) {
    Write-Host "[scheduler] Task '$TaskName' already exists — deleting before re-create."
    schtasks /delete /tn $TaskName /f | Out-Null
}

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Build the command string that schtasks will run.
# We wrap the python call in cmd /c so we can redirect output to the log file.
$PythonArgs = "`"$ScriptPath`" --provider $Provider --limit $Limit"
$CmdStr     = "cmd /c `"$PythonExe $PythonArgs >> `"$LogFile`" 2>&1`""

Write-Host "[scheduler] Registering task:"
Write-Host "  Name    : $TaskName"
Write-Host "  Trigger : every $Interval minutes"
Write-Host "  Command : $PythonExe $PythonArgs"
Write-Host "  Log     : $LogFile"

schtasks /create `
    /tn  $TaskName `
    /tr  $CmdStr `
    /sc  MINUTE `
    /mo  $Interval `
    /f

if ($LASTEXITCODE -ne 0) {
    Write-Error "[scheduler] schtasks /create failed (exit $LASTEXITCODE)."
    exit 1
}

Write-Host "[scheduler] Task '$TaskName' registered successfully."
Write-Host ""
Write-Host "Quick reference:"
Write-Host "  Check state  : .\scripts\install_scheduler.ps1 -Action status"
Write-Host "  Remove task  : .\scripts\install_scheduler.ps1 -Action remove"
Write-Host "  Run now      : python scripts\process_audit_queue.py --provider $Provider --limit $Limit"
