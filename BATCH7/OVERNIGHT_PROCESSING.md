# Overnight Processing Setup

This guide explains how to set up automated overnight processing for the BATCH7 pipeline.

## Overview

The overnight processing system runs the pipeline automatically during off-hours (default: 10 PM - 6 AM) to process documents without interfering with daytime work.

## Quick Setup

### 1. Run the Setup Script

Open PowerShell as Administrator and run:

```powershell
cd BATCH7
.\setup_overnight_processing.ps1
```

### 2. Customize Schedule (Optional)

```powershell
# Custom start and end times
.\setup_overnight_processing.ps1 -StartTime "23:00" -EndTime "07:00"
```

## What Gets Scheduled

Three separate tasks are created:

1. **BATCH7_Overnight_Images** - Processes image files
2. **BATCH7_Overnight_Text** - Processes text files  
3. **BATCH7_Overnight_Natives** - Processes Excel spreadsheets

Each task:
- Runs daily at the specified start time
- Repeats every hour until the end time
- Processes files with `--skip-existing` (won't reprocess completed files)
- Runs hidden (no popup windows)
- Automatically restarts on failure (up to 3 times)

## Default Schedule

- **Start Time:** 10:00 PM (22:00)
- **End Time:** 6:00 AM (06:00)
- **Frequency:** Every hour during the window
- **Duration:** 8 hours total

## How It Works

1. **At Start Time:** Each task begins processing
2. **Every Hour:** Tasks repeat (processes new files since last run)
3. **At End Time:** Tasks stop until next day

This ensures:
- Files are processed continuously overnight
- New files added during the night get picked up
- Processing doesn't interfere with daytime work
- Multiple runs catch any files that failed on first attempt

## Monitoring

### Check Task Status

```powershell
Get-ScheduledTask | Where-Object {$_.TaskName -like 'BATCH7_Overnight_*'} | Format-Table TaskName, State, LastRunTime
```

### View Task History

1. Open **Task Scheduler**
2. Find tasks starting with `BATCH7_Overnight_`
3. Click **History** tab to see run logs

### Check Processing Progress

```powershell
# Count processed image files
(Get-ChildItem BATCH7\IMAGES\001\*.json).Count

# Count processed text files
(Get-ChildItem BATCH7\TEXT\001\*_extraction.json).Count

# Count processed native files
(Get-ChildItem BATCH7\NATIVES\001\*_analysis.json).Count
```

## Manual Control

### Run Tasks Now (Test)

```powershell
Start-ScheduledTask -TaskName "BATCH7_Overnight_Images"
Start-ScheduledTask -TaskName "BATCH7_Overnight_Text"
Start-ScheduledTask -TaskName "BATCH7_Overnight_Natives"
```

### Disable Tasks (Temporarily)

```powershell
Disable-ScheduledTask -TaskName "BATCH7_Overnight_Images"
Disable-ScheduledTask -TaskName "BATCH7_Overnight_Text"
Disable-ScheduledTask -TaskName "BATCH7_Overnight_Natives"
```

### Enable Tasks

```powershell
Enable-ScheduledTask -TaskName "BATCH7_Overnight_Images"
Enable-ScheduledTask -TaskName "BATCH7_Overnight_Text"
Enable-ScheduledTask -TaskName "BATCH7_Overnight_Natives"
```

### Remove Tasks

```powershell
Unregister-ScheduledTask -TaskName "BATCH7_Overnight_Images" -Confirm:$false
Unregister-ScheduledTask -TaskName "BATCH7_Overnight_Text" -Confirm:$false
Unregister-ScheduledTask -TaskName "BATCH7_Overnight_Natives" -Confirm:$false
```

## Troubleshooting

### Tasks Not Running

1. **Check if tasks exist:**
   ```powershell
   Get-ScheduledTask -TaskName "BATCH7_Overnight_*"
   ```

2. **Check if tasks are enabled:**
   ```powershell
   Get-ScheduledTask -TaskName "BATCH7_Overnight_*" | Select-Object TaskName, State
   ```
   State should be "Ready", not "Disabled"

3. **Check Task Scheduler History** for error messages

4. **Verify Python path:**
   ```powershell
   $Task = Get-ScheduledTask -TaskName "BATCH7_Overnight_Images"
   $Task.Actions[0].Execute
   ```

5. **Test manually:**
   ```powershell
   cd BATCH7
   python run_batch7_pipeline.py --process images --skip-existing
   ```

### Tasks Running But Not Processing Files

1. **Check API key** - Make sure `.env` file has `GEMINI_API_KEY`
2. **Check file locations** - Verify files exist in `IMAGES/001/`, `TEXT/001/`, etc.
3. **Check API credits** - Verify you have remaining Gemini API credits
4. **Check logs** - Look for error messages in Task Scheduler History

### Computer Sleeps During Processing

Tasks are configured to:
- Run even if computer is on battery
- Start when computer wakes up (if "Start when available" is enabled)
- Continue processing after wake from sleep

However, if computer is completely shut down, tasks won't run until it's powered on again.

## Integration with Webhook

The overnight processing works alongside the webhook:

- **Overnight Tasks:** Process files continuously
- **Webhook (Every 5 min):** Commits and publishes updates

They work together:
1. Overnight tasks process files → Create JSON outputs
2. Webhook detects changes → Commits and pushes to GitHub
3. Webhook updates README → Shows latest findings

## Best Practices

1. **Start with one task** - Test with images first before enabling all three
2. **Monitor first night** - Check Task Scheduler History after first run
3. **Check API usage** - Monitor Gemini API credit consumption
4. **Keep computer on** - Tasks only run when computer is powered on
5. **Use skip-existing** - Prevents reprocessing completed files (saves API credits)

## Example: Full Setup

```powershell
# 1. Set up overnight processing (10 PM - 6 AM)
cd BATCH7
.\setup_overnight_processing.ps1

# 2. Verify tasks created
Get-ScheduledTask | Where-Object {$_.TaskName -like 'BATCH7_Overnight_*'}

# 3. Test one task manually
Start-ScheduledTask -TaskName "BATCH7_Overnight_Images"

# 4. Check progress after a few minutes
(Get-ChildItem BATCH7\IMAGES\001\*.json).Count

# 5. Tasks will run automatically tonight at 10 PM
```

## Notes

- Tasks use `pythonw.exe` (windowless) so they run silently
- Tasks run with highest privileges
- Tasks automatically restart on failure (up to 3 times)
- Each task processes independently (can run simultaneously)
- Uses `--skip-existing` flag to avoid reprocessing completed files

