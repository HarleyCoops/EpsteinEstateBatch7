# Webhook Quick Start

## Setup in 3 Steps

### 1. Test (Dry Run)
```powershell
cd BATCH7
python auto_commit_webhook.py --dry-run --once
```

### 2. Test (Real Commit)
```powershell
python auto_commit_webhook.py --once
```

### 3. Set Up Scheduler
```powershell
# Run PowerShell as Administrator


```

## Verify It Works

```powershell
# Check task exists
Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"

# Run manually
Start-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"

# Check git log
git log --oneline -5
```

## What It Does

Every 5 minutes, the webhook:
1. Checks for git changes
2. Analyzes new outputs (JSON files, letters, etc.)
3. Generates verbose commit message with findings
4. Commits and pushes to remote

## Commit Message Example

```
Pipeline Update: 2024-01-15 14:30:00

=== LATEST FINDINGS ===

NATIVES PROCESSING:
  • HOUSE_OVERSIGHT_009_analysis.json: 3 worksheets, 15 people, 8 relationships

IMAGES PROCESSING:
  • IMG_001.jpg.json: document, text: YES, 3 people identified

TEXT PROCESSING:
  • Story assembly: 5 letters/stories assembled

LETTERS/STORIES:
  • S0001: text, translated, 12 sources

=== SUMMARY ===
New files: 23
Modified files: 5
```

## Common Commands

```powershell
# Disable temporarily
Disable-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"

# Re-enable
Enable-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"

# Remove completely
Unregister-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook" -Confirm:$false
```

## Full Documentation

See `WEBHOOK_SETUP.md` for detailed setup instructions and troubleshooting.

