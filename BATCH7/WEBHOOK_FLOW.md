# Webhook Flow Diagram

## How the Summary Update Gets Triggered

The summary update script (`generate_readme_summary.py`) is **automatically triggered** by the main webhook script (`auto_commit_webhook.py`). It's not a separate scheduled task - it runs as part of the webhook process.

## Complete Flow (Every 5 Minutes)

```
┌─────────────────────────────────────────────────────────────┐
│ Windows Task Scheduler                                       │
│ Runs every 5 minutes                                        │
│ Command: pythonw.exe auto_commit_webhook.py --once          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ auto_commit_webhook.py                                      │
│ 1. Detects git changes                                      │
│ 2. Analyzes JSON files for findings                          │
│ 3. Generates commit message                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ generate_readme_summary.py                                  │
│ Called via subprocess.run()                                 │
│ - Analyzes recent JSON files                                 │
│ - Extracts Trump mentions, key characters, themes            │
│ - Updates BOTH README.md files with summary                  │
│   (root README.md and BATCH7/README.md)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ auto_commit_webhook.py (continued)                          │
│ 4. Stages all changes (including updated README)            │
│ 5. Commits with verbose message                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ update_readme_status.py                                     │
│ Called via subprocess.run()                                │
│ - Gets latest git commit timestamp                          │
│ - Replaces {LAST_GIT_COMMIT_TIME} in BOTH README files     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ auto_commit_webhook.py (final)                              │
│ 6. Commits timestamp update                                 │
│ 7. Pushes all commits to GitHub                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Points

1. **Single Scheduled Task**: Only one Windows Scheduled Task exists - it runs `auto_commit_webhook.py`

2. **Automatic Chain**: The webhook script automatically calls:
   - `generate_readme_summary.py` (before commit)
   - `update_readme_status.py` (after commit)

3. **No Manual Steps**: Everything happens automatically - you don't need to run `generate_readme_summary.py` manually

4. **Both README Files**: Both scripts update BOTH:
   - `README.md` (root - public-facing)
   - `BATCH7/README.md` (technical)

## Code Reference

In `auto_commit_webhook.py`, line ~451:
```python
# Update summary from JSON files first (needs current files)
summary_generator = base_dir / "BATCH7" / "generate_readme_summary.py"
if summary_generator.exists():
    result = subprocess.run([sys.executable, str(summary_generator)], ...)
```

In `auto_commit_webhook.py`, line ~498:
```python
# Update timestamp with THIS commit's time
readme_updater = base_dir / "BATCH7" / "update_readme_status.py"
if readme_updater.exists():
    result = subprocess.run([sys.executable, str(readme_updater)], ...)
```

## Manual Testing

If you want to test the summary generation manually (without committing):

```powershell
cd BATCH7
python generate_readme_summary.py
```

This will update the README files locally but won't commit anything.

## Troubleshooting

If summaries aren't updating:

1. **Check if webhook is running:**
   ```powershell
   Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
   ```

2. **Check webhook logs** (Task Scheduler → History tab)

3. **Test summary script manually:**
   ```powershell
   python BATCH7/generate_readme_summary.py
   ```

4. **Check if JSON files exist:**
   ```powershell
   ls BATCH7\IMAGES\001\*.json | Select-Object -Last 10
   ls BATCH7\TEXT\001\*_extraction.json | Select-Object -Last 10
   ```

5. **Run webhook manually to see output:**
   ```powershell
   python BATCH7/auto_commit_webhook.py --once
   ```

