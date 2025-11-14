# Auto-Commit Webhook Setup Guide

This guide explains how to set up an automatic commit system that runs every 5 minutes, analyzes pipeline outputs, and commits changes with verbose, time-stamped messages describing the latest findings.

## Overview

The webhook system consists of:
1. **`auto_commit_webhook.py`** - Main script that detects changes, analyzes outputs, and commits
2. **`setup_webhook_scheduler.ps1`** - PowerShell script to set up Windows Task Scheduler
3. **Manual setup options** - Alternative methods for different platforms

## Features

- **Automatic Detection** - Monitors git repository for changes
- **Intelligent Analysis** - Analyzes JSON outputs to extract key findings
- **Verbose Commit Messages** - Time-stamped messages describing:
  - New natives analysis files (worksheets, entities, relationships)
  - New image analysis files (document types, OCR results, entities)
  - New text extractions and story assemblies
  - New letter/story directories with metadata
  - Summary statistics
- **Safe Operation** - Dry-run mode for testing
- **Error Handling** - Continues running even if individual commits fail

## Quick Setup (Windows)

### Method 1: PowerShell Script (Recommended)

1. **Open PowerShell as Administrator**

2. **Run the setup script:**
```powershell
cd BATCH7
.\setup_webhook_scheduler.ps1
```

3. **Customize interval (optional):**
```powershell
.\setup_webhook_scheduler.ps1 -IntervalMinutes 30
```

4. **Test the task:**
```powershell
Start-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### Method 2: Manual Task Scheduler Setup

1. Open **Task Scheduler** (search in Start menu)

2. Click **Create Task** (not Basic Task)

3. **General Tab:**
   - Name: `BATCH7_AutoCommit_Webhook`
   - Description: `Auto-commit webhook for BATCH7 pipeline`
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"

4. **Triggers Tab:**
   - Click **New**
   - Begin: `At startup` or `On a schedule` (choose a start time)
   - Check **Repeat task every**: `5 minutes`
   - Duration: `Indefinitely`

5. **Actions Tab:**
   - Click **New**
   - Action: `Start a program`
   - Program/script: `python` (or full path to Python executable)
   - Add arguments: `"C:\Users\chris\EpsteinEstateBatch7\BATCH7\auto_commit_webhook.py" --once`
   - Start in: `C:\Users\chris\EpsteinEstateBatch7\BATCH7`

6. **Conditions Tab:**
   - Uncheck "Start the task only if the computer is on AC power"
   - Check "Start the task only if the following network connection is available" (optional)

7. **Settings Tab:**
   - Check "Allow task to be run on demand"
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Check "If the task fails, restart every": `1 minute` (up to 3 times)

8. Click **OK** and enter your password if prompted

## Manual Testing

Before setting up the scheduler, test the script manually:

### Dry Run (Safe - No Commits)
```powershell
cd BATCH7
python auto_commit_webhook.py --dry-run --once
```

This will show you what would be committed without actually committing.

### Single Run (Actually Commits)
```powershell
python auto_commit_webhook.py --once
```

### Continuous Loop (For Testing)
```powershell
python auto_commit_webhook.py --interval 5
```

This runs every 5 minutes (useful for testing). Press Ctrl+C to stop.

## Configuration Options

### Command-Line Arguments

```powershell
python auto_commit_webhook.py [OPTIONS]

Options:
  --base-dir PATH      Base directory (default: parent of script directory)
  --dry-run           Show what would be committed without committing
  --interval MINUTES  Interval in minutes for continuous mode (default: 30)
  --once              Run once and exit (for scheduled tasks)
```

### Environment Variables

The script uses the same `.env` file as the main pipeline (if needed for future enhancements).

## Commit Message Format

The webhook generates verbose commit messages like this:

```
Pipeline Update: 2024-01-15 14:30:00

=== LATEST FINDINGS ===

NATIVES PROCESSING:
  • HOUSE_OVERSIGHT_009_analysis.json: 3 worksheets, 15 people, 8 relationships

IMAGES PROCESSING:
  • IMG_001.jpg.json: document, text: YES, 3 people identified
  • IMG_002.jpg.json: photograph, text: NO, 0 people identified

TEXT PROCESSING:
  • Story assembly: 5 letters/stories assembled, 2 unassigned pages

LETTERS/STORIES:
  • S0001: text, translated, 12 sources
  • S0002: text, 8 sources

=== SUMMARY ===
Modified files: 5
New files: 23
Untracked files: 2

Auto-committed at 2024-01-15 14:30:00
```

## Monitoring and Management

### View Task Status
```powershell
Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### View Task History
1. Open **Task Scheduler**
2. Find `BATCH7_AutoCommit_Webhook`
3. Click **History** tab

### Run Task Manually
```powershell
Start-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### Disable Task (Temporarily)
```powershell
Disable-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### Enable Task
```powershell
Enable-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### Remove Task
```powershell
Unregister-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook" -Confirm:$false
```

## Troubleshooting

### Task Not Running

1. **Check if task exists:**
```powershell
Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

2. **Check task history in Task Scheduler** for error messages

3. **Verify Python path** - The task might be using wrong Python executable:
```powershell
# Update task with correct Python path
$Action = New-ScheduledTaskAction -Execute "C:\Python39\python.exe" -Argument "`"$ScriptPath`" --once"
Set-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook" -Action $Action
```

### Git Errors

- **"Not a git repository"** - Make sure you're running from the repository root
- **"Permission denied"** - Check git credentials and remote access
- **"Nothing to commit"** - Normal if no changes detected

### No Changes Detected

The script only commits if there are actual changes. This is normal if:
- Pipeline hasn't run since last commit
- All outputs are already committed
- Files are ignored by `.gitignore`

### Testing Git Push

Make sure your git remote is configured:
```powershell
git remote -v
git push origin main  # Test manual push
```

## Linux/macOS Setup

For Linux/macOS, use cron instead:

### Create Cron Job

1. **Edit crontab:**
```bash
crontab -e
```

2. **Add this line (runs every 5 minutes):**
```
*/5 * * * * cd /path/to/EpsteinEstateBatch7/BATCH7 && /usr/bin/python3 auto_commit_webhook.py --once >> /tmp/batch7_webhook.log 2>&1
```

3. **Or use systemd timer** (more robust):

Create `/etc/systemd/system/batch7-webhook.service`:
```ini
[Unit]
Description=BATCH7 Auto-Commit Webhook
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/EpsteinEstateBatch7/BATCH7
ExecStart=/usr/bin/python3 /path/to/EpsteinEstateBatch7/BATCH7/auto_commit_webhook.py --once
User=your-username
```

Create `/etc/systemd/system/batch7-webhook.timer`:
```ini
[Unit]
Description=BATCH7 Auto-Commit Webhook Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable batch7-webhook.timer
sudo systemctl start batch7-webhook.timer
```

## Security Considerations

- The webhook commits **all changes** in the repository (respects `.gitignore`)
- Make sure sensitive files are in `.gitignore` (like `.env`)
- The script runs with the same permissions as the scheduled task user
- Consider using a dedicated git user/service account for production

## Advanced Usage

### Custom Base Directory

```powershell
python auto_commit_webhook.py --base-dir "C:\Other\Path" --once
```

### Different Interval

```powershell
python auto_commit_webhook.py --interval 60  # Every hour
```

### Integration with Pipeline

You can also call the webhook from your pipeline scripts:

```python
# At the end of run_batch7_pipeline.py
import subprocess
subprocess.run(["python", "auto_commit_webhook.py", "--once"])
```

## Next Steps

1. Test with `--dry-run` first
2. Run manually once to verify it works
3. Set up scheduled task
4. Monitor first few commits to ensure messages are informative
5. Adjust interval if needed (5 minutes is default)

## Support

If you encounter issues:
1. Check the commit messages - they should be informative
2. Review git log to see commit history
3. Check Task Scheduler history for errors
4. Run with `--dry-run` to debug without committing

