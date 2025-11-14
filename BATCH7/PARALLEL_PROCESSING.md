# Running Pipeline Stages in Parallel

Since the three processing streams (NATIVES, IMAGES, TEXT) are independent, you can run them in parallel to speed up processing.

## Quick Start

### Method 1: Separate Terminal Windows (Simplest)

**Terminal 1 - Images:**
```powershell
cd BATCH7
$env:GEMINI_API_KEY="your-api-key"
python run_batch7_pipeline.py --process images --skip-existing
```

**Terminal 2 - Text (run simultaneously):**
```powershell
cd BATCH7
$env:GEMINI_API_KEY="your-api-key"
python run_batch7_pipeline.py --process text --skip-existing
```

### Method 2: PowerShell Background Jobs

```powershell
cd BATCH7

# Start image processing in background
Start-Job -ScriptBlock {
    cd C:\Users\chris\EpsteinEstateBatch7\BATCH7
    $env:GEMINI_API_KEY="your-api-key"
    python run_batch7_pipeline.py --process images --skip-existing
} -Name "Images"

# Start text processing in background
Start-Job -ScriptBlock {
    cd C:\Users\chris\EpsteinEstateBatch7\BATCH7
    $env:GEMINI_API_KEY="your-api-key"
    python run_batch7_pipeline.py --process text --skip-existing
} -Name "Text"

# Check status
Get-Job

# View output from a job
Receive-Job -Name "Images"
Receive-Job -Name "Text"

# Wait for all jobs
Get-Job | Wait-Job

# Clean up
Get-Job | Remove-Job
```

### Method 3: Helper Script

Use the `run_parallel.ps1` script:

```powershell
cd BATCH7
.\run_parallel.ps1 -Process images,text -SkipExisting
```

This will:
- Start both processes in background jobs
- Monitor progress
- Show results when complete

## Benefits of Parallel Processing

- **Faster Processing** - Multiple streams run simultaneously
- **Better Resource Utilization** - Uses multiple API calls concurrently
- **Independent Progress** - Each stream processes independently
- **Safe** - Uses `--skip-existing` to avoid conflicts

## Important Notes

1. **API Rate Limits** - Running in parallel uses more API calls per minute. Monitor your Gemini API quota.

2. **File Conflicts** - The `--skip-existing` flag ensures already-processed files are skipped, preventing conflicts.

3. **Output Directories** - Each stream writes to separate output directories:
   - Images → `output/images_analysis/` (actually saved alongside images)
   - Text → `output/text_analysis/`
   - Natives → `output/natives_analysis/`

4. **Git Commits** - The webhook will commit changes from all streams as they complete.

## Monitoring Parallel Jobs

```powershell
# List all jobs
Get-Job

# View specific job output
Receive-Job -Name "Process_images"

# Check job state
(Get-Job -Name "Process_images").State

# Stop a job if needed
Stop-Job -Name "Process_images"
```

## Example: Run All Three in Parallel

```powershell
cd BATCH7
.\run_parallel.ps1 -Process natives,images,text -SkipExisting
```

This will start all three processing streams simultaneously.

