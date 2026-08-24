# Daily PSX price backfill, run by the "PSX Price Backfill" Windows Scheduled Task
# (see backend/scripts/register_price_backfill_task.ps1) so app/ingestion/psx_prices.py
# gets run on a schedule instead of only when someone remembers to -- it went a month
# stale in exactly that way before this was set up (2026-07-24 to 2026-08-24, discovered
# and manually backfilled 2026-08-23).
#
# years=1/sector=all is deliberately generous: backfill_security_prices only inserts
# dates not already on file (checked against the uq_price_ohlcv_security_date
# constraint too), so re-fetching a wide window daily is safe and cheap, not wasteful --
# it just re-confirms most of the year is already there and inserts whatever's new.

# Deliberately NOT $ErrorActionPreference = "Stop": Python's logging module writes its
# INFO records to stderr, and redirecting a native command's stderr in PowerShell wraps
# each line in a NativeCommandError -- combined with -Stop, that turned the *first* log
# line the backfill printed into a terminating error, which the old try/catch here
# swallowed and logged as "FAILED" after doing almost nothing, while still exiting 0 (a
# real incident: the very first scheduled/manual test run of this script did exactly
# that, appearing to "succeed" while the backfill barely started). Checking the real
# python.exe exit code via $LASTEXITCODE afterward is the correct signal, not exceptions.
$backendDir = "D:\khronos\psx-fertilizer\backend"
$logDir = Join-Path $backendDir "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "price_backfill.log"

Set-Location $backendDir
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "===== $timestamp =====" -Encoding utf8

# 2>&1 | Out-File -Encoding utf8, not *>> -- *>> writes UTF-16LE for a redirected native
# command's streams on Windows PowerShell 5.1 (confirmed: a real early test run of this
# script produced a log file that was unreadable garbage -- every character spaced out
# with nulls -- for exactly this reason), inconsistent with Add-Content's utf8 above.
& "$backendDir\.venv\Scripts\python.exe" -m app.ingestion.psx_prices 1 all 2>&1 |
    Out-File -FilePath $logFile -Append -Encoding utf8
$exitCode = $LASTEXITCODE
Add-Content -Path $logFile -Value "===== exit code $exitCode =====" -Encoding utf8
exit $exitCode
