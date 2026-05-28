<#
.SYNOPSIS
    Idempotently registers, updates, or removes ALL LaunchLook scheduled
    tasks in Windows Task Scheduler.

.DESCRIPTION
    Wraps schtasks.exe so you never have to hand-write the commands again.
    Safe to run multiple times: deletes and re-creates tasks that already
    exist, so config changes always take effect.

    Tasks registered:
      LaunchLook Audit Queue    - process_audit_queue.py    every 30 min
      LaunchLook Stale Alert    - stale_queue_alert.py      every 6 hours
      LaunchLook Follow-up      - followup_email.py         daily at 09:00
      LaunchLook Heartbeat      - queue_heartbeat.py        weekly Sunday 08:00
      LaunchLook Weekly Digest  - weekly_digest.py          weekly Sunday 08:15

.PARAMETER Action
    install  - Register (or update) all tasks. Default.
    remove   - Delete all tasks.
    status   - Print current task states without modifying anything.

.PARAMETER Interval
    How often the audit queue task fires, in minutes. Default: 30.

.PARAMETER Provider
    LLM provider to pass to process_audit_queue.py. Default: gpt.

.PARAMETER Limit
    Max jobs per audit queue run. Default: 3.

.EXAMPLE
    # Register all tasks
    .\scripts\install_scheduler.ps1

    # Remove all tasks
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

$RepoRoot   = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PythonExe  = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $PythonExe) { $PythonExe = 'python' }
$LogDir     = Join-Path $RepoRoot 'logs'

# All tasks managed by this script
$Tasks = @(
    @{
        Name    = 'LaunchLook Audit Queue'
        Script  = 'scripts\process_audit_queue.py'
        Args    = "--provider $Provider --limit $Limit"
        Sc      = 'MINUTE'
        Mo      = "$Interval"
        LogFile = 'scheduler.log'
        Label   = "every $Interval min"
    },
    @{
        Name    = 'LaunchLook Stale Alert'
        Script  = 'scripts\stale_queue_alert.py'
        Args    = '--hours 48'
        Sc      = 'HOURLY'
        Mo      = '6'
        LogFile = 'stale_alert.log'
        Label   = 'every 6 hours'
    },
    @{
        Name    = 'LaunchLook Follow-up'
        Script  = 'scripts\followup_email.py'
        Args    = ''
        Sc      = 'DAILY'
        Mo      = '1'
        St      = '09:00'
        LogFile = 'followup.log'
        Label   = 'daily 09:00'
    },
    @{
        Name    = 'LaunchLook Heartbeat'
        Script  = 'scripts\queue_heartbeat.py'
        Args    = ''
        Sc      = 'WEEKLY'
        D       = 'SUN'
        St      = '08:00'
        LogFile = 'heartbeat.log'
        Label   = 'weekly Sun 08:00'
    },
    @{
        Name    = 'LaunchLook Weekly Digest'
        Script  = 'scripts\weekly_digest.py'
        Args    = ''
        Sc      = 'WEEKLY'
        D       = 'SUN'
        St      = '08:15'
        LogFile = 'weekly_digest.log'
        Label   = 'weekly Sun 08:15'
    }
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
function Get-TaskExists($Name) {
    schtasks /query /tn $Name 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Remove-Task($Name) {
    if (Get-TaskExists $Name) {
        schtasks /delete /tn $Name /f | Out-Null
        Write-Host "[scheduler] Removed '$Name'."
    }
}

function Register-Task($t) {
    $ScriptPath = Join-Path $RepoRoot $t.Script
    $Args       = if ($t.Args) { " $($t.Args)" } else { '' }
    $LogFile    = Join-Path $LogDir $t.LogFile
    $CmdStr     = "cmd /c `"$PythonExe `"$ScriptPath`"$Args >> `"$LogFile`" 2>&1`""

    # Build schtasks argument list dynamically
    $sargs = @('/create', '/tn', $t.Name, '/tr', $CmdStr, '/sc', $t.Sc, '/f')
    if ($t.Mo)  { $sargs += @('/mo', $t.Mo) }
    if ($t.D)   { $sargs += @('/d',  $t.D) }
    if ($t.St)  { $sargs += @('/st', $t.St) }

    & schtasks @sargs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[scheduler] schtasks /create failed for '$($t.Name)' (exit $LASTEXITCODE)."
        exit 1
    }
    Write-Host "[scheduler] Registered '$($t.Name)' ($($t.Label)) -> $($t.LogFile)"
}

# ------------------------------------------------------------------
# status
# ------------------------------------------------------------------
if ($Action -eq 'status') {
    foreach ($t in $Tasks) {
        if (Get-TaskExists $t.Name) {
            Write-Host "[scheduler] REGISTERED  : $($t.Name) ($($t.Label))"
        } else {
            Write-Host "[scheduler] NOT FOUND   : $($t.Name)"
        }
    }
    exit 0
}

# ------------------------------------------------------------------
# remove
# ------------------------------------------------------------------
if ($Action -eq 'remove') {
    foreach ($t in $Tasks) { Remove-Task $t.Name }
    Write-Host "[scheduler] All LaunchLook tasks removed."
    exit 0
}

# ------------------------------------------------------------------
# install (idempotent: remove first, then create all)
# ------------------------------------------------------------------
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Write-Host "[scheduler] Installing $($Tasks.Count) LaunchLook task(s)..."
foreach ($t in $Tasks) {
    Remove-Task $t.Name
    Register-Task $t
}

Write-Host ""
Write-Host "[scheduler] All tasks registered. Quick reference:"
Write-Host "  Check state : .\scripts\install_scheduler.ps1 -Action status"
Write-Host "  Remove all  : .\scripts\install_scheduler.ps1 -Action remove"
Write-Host "  Run queue   : python scripts\process_audit_queue.py --provider $Provider --limit $Limit"
Write-Host "  Run digest  : python scripts\weekly_digest.py --dry-run"
