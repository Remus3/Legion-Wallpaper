# headless_run.ps1 - relaunch-on-crash wrapper for the headless autonomous run.
#
# WHY: a headless run dies for reasons that have nothing to do with the work -
# an API 400, a dropped socket, a cascade-cancel. Relaunching by hand defeats
# the point of an unattended run, and relaunching blind would redo slices that
# already merged, so every relaunch first asks slice_orchestrator.py which
# slices are still owed and stops when the answer is none.
#
# ASCII only, no em-dashes, no smart quotes: PS 5.1 ANSI-decodes a no-BOM .ps1,
# so a UTF-8 em-dash inside a double-quoted string arrives as a string-
# terminating smart quote and cascades into a parse failure (2026-05-18
# boot-script incident). Stop-Process is never used - it hangs the MCP pipe;
# taskkill /F is the sanctioned kill.

[CmdletBinding()]
param(
    [int]$MaxRetries = 5,
    [string]$Prompt = "/headless-upgrade",
    [int]$TimeoutMinutes = 240,
    [string]$ClaudeExe = "claude"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Absolute, derived from this script's own location - never from the caller's cwd.
$Root = Split-Path -Parent $PSScriptRoot
$pinned = Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"
$Python = if (Test-Path $pinned) { $pinned } else { (Get-Command python).Source }
$Orchestrator = Join-Path $Root "tools\slice_orchestrator.py"
# Every headless claude goes through MAIN's fleet kit (kit v3, 2026-10-03).
# This run is hours long with a live console, which the kit's synchronous,
# output-capturing spawn cannot carry, so it uses lw_headless_env.py exec: the
# kit's gate (CLAUDE_HEADLESS_BASE_URL, registry first, loopback, port probed),
# the kit's child env, its 120-run budget, status file and usage line, and
# kit.claude_exe for a bare "claude". Exit 78 without starting claude on any
# refusal. bare is NOT used: LW's floors live in hooks.
$HeadlessEnv = Join-Path $Root "tools\lw_headless_env.py"
$RefusedExit = 78
$LogDir = Join-Path $Root "logs"

# A caller-supplied retry count is still bounded here: an unattended wrapper that
# can be told to retry forever is a spin loop burning the operator's quota.
if ($MaxRetries -lt 0) { $MaxRetries = 0 }
if ($MaxRetries -gt 20) { $MaxRetries = 20 }

function Write-RunLog([string]$Message) {
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir | Out-Null
    }
    $logFile = Join-Path $LogDir ((Get-Date -Format "yyyy-MM-dd") + ".log")
    $line = "{0} headless_run {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $logFile -Value $line -Encoding ascii
    Write-Host $line
}

function Get-OwedSlices {
    # resume exits 0 even with no manifest, so stdout is the whole signal.
    $lines = & $Python $Orchestrator resume
    return @($lines | Where-Object { $_ -and $_.ToString().Trim() -ne "" })
}

function Format-NativeArg([string]$a) {
    # Start-Process joins -ArgumentList with bare spaces and quotes nothing, so
    # the repo root (it contains a space) would split into two arguments.
    # Standard Windows argv quoting: double backslashes that precede a quote or
    # the closing quote, escape the quote itself.
    if ($a -ne "" -and $a -notmatch '[\s"]') { return $a }
    $escaped = $a -replace '(\\*)"', '$1$1\"'
    $escaped = $escaped -replace '(\\+)$', '$1$1'
    return '"' + $escaped + '"'
}

function Invoke-HeadlessRun {
    # Returns "" on a clean exit, "REFUSED" when the proxy gate refused the
    # spawn, otherwise the crash reason to log.
    $claudeArgs = @("-p", $Prompt, "--permission-mode", "bypassPermissions")
    # ONE interactive governor slot for the run (FLEET-KIT v6 ruling: code-writing
    # runs take one slot at the call); none free in 30 min = REFUSED (78).
    $gateArgs = @($HeadlessEnv, "exec", "--governor", "interactive", "--governor-timeout", "1800", "--", $ClaudeExe) + $claudeArgs
    $argLine = ($gateArgs | ForEach-Object { Format-NativeArg $_ }) -join " "
    $proc = Start-Process -FilePath $Python -ArgumentList $argLine `
        -WorkingDirectory $Root -NoNewWindow -PassThru
    if (-not $proc.WaitForExit($TimeoutMinutes * 60 * 1000)) {
        # /T: the gate is the parent now, so the claude under it dies too.
        & taskkill /F /T /PID $proc.Id | Out-Null
        return "timeout after $TimeoutMinutes min (pid $($proc.Id) taskkilled)"
    }
    if ($proc.ExitCode -eq $RefusedExit) {
        return "REFUSED"
    }
    if ($proc.ExitCode -ne 0) {
        return "exit code $($proc.ExitCode)"
    }
    return ""
}

$attempt = 0
$reason = ""
while ($true) {
    $attempt++
    $owed = Get-OwedSlices
    if ($attempt -eq 1) {
        Write-RunLog "start attempt 1 owed=$($owed.Count) prompt=$Prompt"
    } else {
        Write-RunLog "relaunch attempt $attempt/$($MaxRetries + 1) reason=$reason owed=$($owed.Count)"
        if ($owed.Count -eq 0) {
            Write-RunLog "no slices owed after the crash - checkpoint is complete, stopping"
            exit 0
        }
        foreach ($slice in $owed) { Write-RunLog "owed: $slice" }
    }

    $reason = Invoke-HeadlessRun
    if ($reason -eq "") {
        Write-RunLog "clean exit on attempt $attempt"
        exit 0
    }
    if ($reason -eq "REFUSED") {
        # FAIL CLOSED and never retried: a relaunch would hit the same refusal,
        # and a plain claude in its place is exactly what the gate forbids. The
        # gate already logged why (unset / host:port / connect refused).
        Write-RunLog "headless spawn REFUSED by the proxy gate - not relaunching"
        exit $RefusedExit
    }
    if ($attempt -gt $MaxRetries) {
        Write-RunLog "GIVING UP after $attempt attempt(s) - last reason=$reason"
        exit 1
    }
    Start-Sleep -Seconds 15
}
