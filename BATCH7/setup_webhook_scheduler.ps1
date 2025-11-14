# PowerShell script to set up Windows Task Scheduler for auto-commit webhook
# Run this script as Administrator to set up the scheduled task

param(
    [string]$PythonPath = "python",
    [string]$ScriptPath = "",
    [int]$IntervalMinutes = 5
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($ScriptPath)) {
    $ScriptPath = Join-Path $ScriptDir "auto_commit_webhook.py"
}

# Verify script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "Error: Script not found at $ScriptPath" -ForegroundColor Red
    exit 1
}

# Get Python executable
$PythonExe = (Get-Command $PythonPath -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-Host "Error: Python not found. Please specify --PythonPath or ensure python is in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Setting up scheduled task..." -ForegroundColor Green
Write-Host "  Python: $PythonExe"
Write-Host "  Script: $ScriptPath"
Write-Host "  Interval: $IntervalMinutes minutes"

# Task name
$TaskName = "BATCH7_AutoCommit_Webhook"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action (run Python script)
# Use pythonw.exe if available (runs without window), otherwise use python.exe
$PythonExeHidden = $PythonExe -replace "python\.exe$", "pythonw.exe"
if (-not (Test-Path $PythonExeHidden)) {
    $PythonExeHidden = $PythonExe
    Write-Host "Note: pythonw.exe not found, using python.exe (may show window)" -ForegroundColor Yellow
}

$Action = New-ScheduledTaskAction -Execute $PythonExeHidden -Argument "`"$ScriptPath`" --once" -WorkingDirectory $ScriptDir

# Create trigger (every 5 minutes)
# Start immediately, repeat every IntervalMinutes, for 365 days
$StartTime = Get-Date
$RepetitionInterval = New-TimeSpan -Minutes $IntervalMinutes
$RepetitionDuration = New-TimeSpan -Days 365
$Trigger = New-ScheduledTaskTrigger -Once -At $StartTime -RepetitionInterval $RepetitionInterval -RepetitionDuration $RepetitionDuration

# Create principal (run whether user is logged on or not, highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

# Create settings (run hidden, don't stop on battery, start when available)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Auto-commit webhook for BATCH7 pipeline - commits changes every $IntervalMinutes minutes" | Out-Null
    Write-Host "`nScheduled task created successfully!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Runs: Every $IntervalMinutes minutes"
    Write-Host "  Command: $PythonExeHidden `"$ScriptPath`" --once"
    Write-Host "  Runs Hidden: Yes (no popup window)"
    Write-Host "  Runs When Computer Off: No (requires computer to be on)"
    Write-Host "`nTo manage the task:" -ForegroundColor Yellow
    Write-Host "  View: Get-ScheduledTask -TaskName $TaskName"
    Write-Host "  Run now: Start-ScheduledTask -TaskName $TaskName"
    Write-Host "  Disable: Disable-ScheduledTask -TaskName $TaskName"
    Write-Host "  Remove: Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
} catch {
    Write-Host "Error creating scheduled task: $_" -ForegroundColor Red
    Write-Host "`nMake sure you're running PowerShell as Administrator!" -ForegroundColor Yellow
    exit 1
}

