# weekly_hygiene_run.ps1 - unattended weekly /weekly-hygiene pass on Legion.
#
# Documented scheduled-task name: LW-WeeklyHygiene (Sunday 04:17, after any
# nightly maintenance tasks so the anomaly-triage step sees fresh scheduled-task
# results). NOTE: the task name is a documented convention only - this file does
# NOT register the task; register it deliberately when LW's weekly schedule is
# set up. Runs Claude Code headless against the repo: the /weekly-hygiene skill
# does its relocate-only doc trims + memory staleness scan + session-start
# anomaly triage, then appends a dated entry to WAKEUP_NOTES.md so the operator
# sees flagged items at next session start. Mirrors the repo's headless
# `claude -p` invocation pattern (RC lineage: tools/headless_run.ps1).
#
# Usage (manual):
#   powershell -ExecutionPolicy Bypass -File "<repo root>\tools\weekly_hygiene_run.ps1"

# No -Model parameter since fleet kit v3 (2026-10-03): the kit picks the model
# from writes_code, and this pass is relocate-only trims + a staleness scan,
# not code, so it runs on the kit's sonnet.

$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

# RUN RECORD (ingest P0-4): one line per run in ops/runtime/runlog/LW-WeeklyHygiene.jsonl,
# read by tools\lw_job_health.py. The job is judged by the status it records, not its
# exit code. Every value goes to Python as an ARGUMENT, never through stdin.
$runStarted = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
function Write-RunRecord([string]$Status, [string]$Detail) {
    $pin = Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"
    $py = if (Test-Path $pin) { $pin } else { (Get-Command python).Source }
    & $py (Join-Path $repo "tools\lw_runlog.py") --task "LW-WeeklyHygiene" --started $runStarted --status $Status --detail $Detail | Out-Null
}

# KILL SWITCH, checked BEFORE claude is invoked and before anything is written.
# Same convention as the other two headless lanes (ops\runtime\inbox_responder\HALT,
# ops\runtime\ci_watchdog\HALT): an EMPTY file still halts, because
# `type nul > HALT` is how an operator makes one under stress and reading that
# as "no halt" would disarm the switch exactly when it is being used. This lane
# spawns `claude -p --dangerously-skip-permissions` with nobody watching, and
# until 2026-09-11 it was the one headless lane here with no way to stop it
# short of unregistering the task.
$halt = Join-Path $repo "ops\runtime\weekly_hygiene\HALT"
if (Test-Path -LiteralPath $halt) {
    $reason = (Get-Content -LiteralPath $halt -Raw -ErrorAction SilentlyContinue)
    if ([string]::IsNullOrWhiteSpace($reason)) { $reason = "HALT file present" }
    Write-Host "[weekly_hygiene] HALT: $($reason.Trim())"
    Write-RunRecord "halted" "HALT file present"
    exit 0
}

$stamp = Get-Date -Format "yyyy-MM-dd"
$log   = Join-Path $repo "logs\weekly_hygiene_$stamp.log"

# PROMISE WATCH (ingest P1-3): keep the CLAUDE.md "Reverse if" promises
# without anyone remembering. Posts once per marker to
# ops\runtime\promises\posts.jsonl; exit 2 means a probe could not decide and is
# logged, never read as "nothing changed". Runs before claude so the pass below
# can list new posts in its WAKEUP entry. Argv only, no shell, no stdin.
$pwPin = Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"
$pwPy = if (Test-Path $pwPin) { $pwPin } else { (Get-Command python).Source }
$pwOut = & $pwPy (Join-Path $repo "tools\lw_promise_watch.py") --post 2>&1
$pwRc = $LASTEXITCODE
Add-Content -LiteralPath $log -Value ("[promise_watch] rc=" + $pwRc + " " + ($pwOut -join " ")) -Encoding ASCII

$prompt = @'
Run /weekly-hygiene. This is an UNATTENDED scheduled run - no operator is
watching the chat. After the pass, append a short dated "weekly-hygiene"
entry to WAKEUP_NOTES.md listing (a) what you relocated and committed and
(b) every judgment call you flagged (memory suspects, actionable anomalies),
so I see them at next session start. Commit + push the relocate-only doc
trims and the WAKEUP entry when local checks are green, then exit. Do NOT
make code changes and do NOT run /sync-all-md. Also list, in that entry, every
line added this week to ops/runtime/promises/posts.jsonl (a CLAUDE.md
"Reverse if" condition came true) and any "[promise_watch] rc=2" line in
today's weekly_hygiene log (a promise could not be checked).
'@

$tools = "Edit,Read,Write,Bash,Grep,Glob,TaskCreate,TaskUpdate,TaskList"

# Every headless claude goes through MAIN's fleet kit (kit v3, 2026-10-03):
# lw_headless_env.py spawn calls fleet_headless.spawn - proxy from the user
# variable CLAUDE_HEADLESS_BASE_URL (registry first), fail closed, the rolling
# 120-run budget, lean flags, no console, one usage line, the live status file.
# It exits 78 without starting claude on any refusal. bare is NOT used: LW's
# floors live in hooks. The prompt goes through a file, never the command line,
# because PS 5.1 mangles embedded double quotes in a native argument.
# Pinned interpreter resolved from LOCALAPPDATA, the same way headless_run.ps1
# does it - never a literal account path in a tracked file.
$pinned = Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"
$Python = if (Test-Path $pinned) { $pinned } else { (Get-Command python).Source }
$HeadlessEnv = Join-Path $repo "tools\lw_headless_env.py"
$RefusedExit = 78
$promptDir = Join-Path $repo "ops\runtime\weekly_hygiene"
if (-not (Test-Path -LiteralPath $promptDir)) {
    New-Item -ItemType Directory -Path $promptDir | Out-Null
}
$promptFile = Join-Path $promptDir "prompt.txt"
$promptTmp = $promptFile + ".tmp"
[System.IO.File]::WriteAllText($promptTmp, ($prompt -replace "`r`n", "`n"), (New-Object System.Text.UTF8Encoding($false)))
Move-Item -LiteralPath $promptTmp -Destination $promptFile -Force

Write-Host "[weekly_hygiene] $stamp start (kit spawn)"
$out = & $Python $HeadlessEnv spawn --note weekly-hygiene --prompt-file $promptFile -- --allowedTools $tools --dangerously-skip-permissions *>&1 |
    Tee-Object -FilePath $log
$code = $LASTEXITCODE
Write-Host "[weekly_hygiene] exit=$code log=$log"

# FAIL CLOSED: a refused spawn is not a transient and is never retried another
# way. It exits 78 so the scheduled task reads red until the proxy is back.
if ($code -eq $RefusedExit) {
    Write-Host "[weekly_hygiene] REFUSED: headless spawn refused by the fleet kit - claude was not started."
    Write-RunRecord "failed" "headless spawn refused by the fleet kit"
    exit $RefusedExit
}

# A weekly maintenance pass that fails ONLY because the Anthropic account hit a
# transient billing / availability limit (credit exhausted, rate limit, 429 /
# 529 overloaded) is not a repo fault. Leaving the task red on that condition
# fires a false anomaly at every session-start probe until the next weekly run.
# Detect the transient class, log it loudly, and exit 0 (it self-resolves).
# Pattern inherited from the RC lineage's gemini-wrapper credit-depletion
# hardening. The detection scans the captured in-memory stream (not the on-disk
# log) to dodge the UTF-16/BOM re-read encoding pitfall.
if ($code -ne 0) {
    $text = ($out | Out-String)
    $transient = 'credit balance is too low|rate limit|rate_limit|overloaded|too many requests|status(?: code)? (?:429|529)|insufficient (?:credit|quota)'
    if ($text -imatch $transient) {
        Write-Host "[weekly_hygiene] SKIPPED: transient Anthropic API condition (credit/rate/availability) - not a hygiene failure; exiting 0 so the scheduled task is not falsely red."
        Write-RunRecord "partial" "transient API condition - pass not run"
        exit 0
    }
}
if ($code -eq 0) { Write-RunRecord "ok" "" } else { Write-RunRecord "failed" "exit $code" }
exit $code
