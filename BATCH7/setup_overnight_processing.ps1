# PowerShell script to set up Windows Task Scheduler for overnight pipeline processing
# Run this script as Administrator to set up the scheduled tasks

param(
    [string]$PythonPath = "python",
    [string]$BaseDir = "",
    [string]$StartTime = "22:00",  # 10 PM
    [string]$EndTime = "06:00"      # 6 AM
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($BaseDir)) {
    $BaseDir = Split-Path -Parent $ScriptDir
}

# Get Python executable
$PythonExe = (Get-Command $PythonPath -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-Host "Error: Python not found. Please specify --PythonPath or ensure python is in PATH" -ForegroundColor Red
    exit 1
}

# Use pythonw.exe if available (runs without window)
$PythonExeHidden = $PythonExe -replace "python\.exe$", "pythonw.exe"
if (-not (Test-Path $PythonExeHidden)) {
    $PythonExeHidden = $PythonExe
    Write-Host "Note: pythonw.exe not found, using python.exe" -ForegroundColor Yellow
}

Write-Host "Setting up overnight processing tasks..." -ForegroundColor Green
Write-Host "  Python: $PythonExeHidden"
Write-Host "  Base Directory: $BaseDir"
Write-Host "  Processing Window: $StartTime - $EndTime"

# Task names
$Tasks = @(
    @{
        Name = "BATCH7_Overnight_Images"
        Description = "Process images overnight - runs continuously from $StartTime to $EndTime"
        Script = "run_batch7_pipeline.py"
        Args = "--process images --skip-existing"
    },
    @{
        Name = "BATCH7_Overnight_Text"
        Description = "Process text files overnight - runs continuously from $StartTime to $EndTime"
        Script = "run_batch7_pipeline.py"
        Args = "--process text --skip-existing"
    },
    @{
        Name = "BATCH7_Overnight_Natives"
        Description = "Process natives (Excel) overnight - runs continuously from $StartTime to $EndTime"
        Script = "run_batch7_pipeline.py"
        Args = "--process natives --skip-existing"
    }
)

foreach ($TaskConfig in $Tasks) {
    $TaskName = $TaskConfig.Name
    $TaskDescription = $TaskConfig.Description
    $ScriptName = $TaskConfig.Script
    $ScriptArgs = $TaskConfig.Args
    
    $ScriptPath = Join-Path $ScriptDir $ScriptName
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "Warning: Script not found at $ScriptPath, skipping task $TaskName" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "`nSetting up task: $TaskName" -ForegroundColor Cyan
    
    # Check if task already exists
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "  Task already exists. Removing old task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create action (run Python script)
    $Action = New-ScheduledTaskAction -Execute $PythonExeHidden -Argument "`"$ScriptPath`" $ScriptArgs" -WorkingDirectory $ScriptDir
    
    # Create trigger - daily at start time, repeat every hour until end time
    $StartDateTime = Get-Date $StartTime
    $EndDateTime = Get-Date $EndTime
    if ($EndDateTime -lt $StartDateTime) {
        # End time is next day
        $EndDateTime = $EndDateTime.AddDays(1)
    }
    
    # Calculate duration
    $Duration = $EndDateTime - $StartDateTime
    
    # Create daily trigger starting at StartTime
    $Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
    
    # Set repetition: every hour for the duration
    $Trigger.Repetition.Interval = "PT1H"  # Every 1 hour
    $Trigger.Repetition.Duration = "PT$($Duration.TotalHours)H"  # Duration in hours
    $Trigger.Repetition.StopAtDurationEnd = $true
    
    # Create principal (run whether user is logged on or not, highest privileges)
    $Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest
    
    # Create settings (run hidden, don't stop on battery, start when available)
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
    
    # Register the task
    try {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $TaskDescription | Out-Null
        Write-Host "  Task created successfully!" -ForegroundColor Green
    } catch {
        Write-Host "  Error creating task: $_" -ForegroundColor Red
        Write-Host "  Make sure you're running PowerShell as Administrator!" -ForegroundColor Yellow
    }
}

Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "Overnight Processing Tasks Setup Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green

Write-Host "`nTask Details:" -ForegroundColor Cyan
foreach ($TaskConfig in $Tasks) {
    Write-Host "  - $($TaskConfig.Name): $($TaskConfig.Description)"
}

Write-Host "`nTo manage tasks:" -ForegroundColor Yellow
Write-Host "  View all: Get-ScheduledTask | Where-Object {$_.TaskName -like 'BATCH7_Overnight_*'}"
Write-Host "  Run now: Start-ScheduledTask -TaskName 'BATCH7_Overnight_Images'"
Write-Host "  Disable: Disable-ScheduledTask -TaskName 'BATCH7_Overnight_Images'"
Write-Host "  Remove: Unregister-ScheduledTask -TaskName 'BATCH7_Overnight_Images' -Confirm:`$false"

Write-Host "`nTasks will run daily from $StartTime to $EndTime" -ForegroundColor Green
Write-Host "Each task runs every hour during this window" -ForegroundColor Green

