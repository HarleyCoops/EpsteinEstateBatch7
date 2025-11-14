# PowerShell script to run multiple pipeline stages in parallel
# Usage: .\run_parallel.ps1 -Process images,text

param(
    [string[]]$Process = @("images", "text"),
    [switch]$SkipExisting = $true
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    Write-Host "Error: Python not found" -ForegroundColor Red
    exit 1
}

# Check API key
if (-not $env:GEMINI_API_KEY) {
    Write-Host "Error: GEMINI_API_KEY not set" -ForegroundColor Red
    exit 1
}

Write-Host "Starting parallel processing..." -ForegroundColor Green
Write-Host "Processes: $($Process -join ', ')" -ForegroundColor Cyan

$Jobs = @()

foreach ($proc in $Process) {
    Write-Host "`nStarting $proc processing in background..." -ForegroundColor Yellow
    
    $Job = Start-Job -ScriptBlock {
        param($ProcessType, $ScriptDir, $PythonExe, $SkipExisting)
        
        Set-Location $ScriptDir
        $env:GEMINI_API_KEY = $using:env:GEMINI_API_KEY
        
        $args = @("run_batch7_pipeline.py", "--process", $ProcessType)
        if ($SkipExisting) {
            $args += "--skip-existing"
        }
        
        & $PythonExe $args
    } -ArgumentList $proc, $ScriptDir, $PythonExe, $SkipExisting.IsPresent -Name "Process_$proc"
    
    $Jobs += $Job
    Write-Host "Started job: $($Job.Name) (ID: $($Job.Id))" -ForegroundColor Green
}

Write-Host "`nAll jobs started. Monitoring progress..." -ForegroundColor Cyan
Write-Host "Use 'Get-Job' to check status, 'Receive-Job -Name Process_<type>' to view output" -ForegroundColor Gray
Write-Host "`nWaiting for jobs to complete..." -ForegroundColor Yellow

# Wait for all jobs with progress indicator
$Completed = 0
while ($Jobs | Where-Object { $_.State -eq 'Running' }) {
    Start-Sleep -Seconds 5
    $Running = ($Jobs | Where-Object { $_.State -eq 'Running' }).Count
    $Completed = $Jobs.Count - $Running
    Write-Host "Progress: $Completed/$($Jobs.Count) completed, $Running running..." -ForegroundColor Cyan
}

Write-Host "`nAll jobs completed!" -ForegroundColor Green

# Show results
foreach ($Job in $Jobs) {
    Write-Host "`n=== $($Job.Name) Results ===" -ForegroundColor Yellow
    Receive-Job -Job $Job
    Remove-Job -Job $Job
}

Write-Host "`nParallel processing complete!" -ForegroundColor Green

