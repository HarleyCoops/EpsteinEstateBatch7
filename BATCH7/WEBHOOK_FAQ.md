# Webhook FAQ

## Will the webhook run if my computer is off?

**No.** Windows Scheduled Tasks only run when your computer is powered on and running. The task will:
- Run every 5 minutes while your computer is on
- Pause when your computer is sleeping/hibernating
- Resume automatically when your computer wakes up (if "Start when available" is enabled)
- Not run at all if your computer is completely shut down

### Options for 24/7 Operation:

1. **Keep your computer on** - Simplest solution, but uses power
2. **Use a cloud server** - Deploy to AWS, Azure, or similar (requires setup)
3. **Use a Raspberry Pi or small server** - Low-power always-on device
4. **Use GitHub Actions** - Free CI/CD that runs in the cloud (requires different setup)

## How do I prevent the popup window every 5 minutes?

The scheduled task is configured to run **hidden** (no popup window). The setup script uses `pythonw.exe` instead of `python.exe` to run without showing a window.

### If you're still seeing popups:

1. **Re-run the setup script** to update the task configuration:
   ```powershell
   cd BATCH7
   .\setup_webhook_scheduler.ps1
   ```

2. **Manually verify the task is configured correctly:**
   ```powershell
   Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook" | Get-ScheduledTaskInfo
   ```

3. **Check Task Scheduler settings:**
   - Open Task Scheduler
   - Find `BATCH7_AutoCommit_Webhook`
   - Right-click → Properties
   - General tab: Check "Hidden" is enabled
   - Settings tab: Verify "Run task as soon as possible after a scheduled start is missed"

### If pythonw.exe is not available:

The script will fall back to `python.exe` which may show a window. To fix this:

1. **Find your Python installation:**
   ```powershell
   where.exe python
   ```

2. **Check if pythonw.exe exists** in the same directory

3. **If pythonw.exe doesn't exist**, you can:
   - Reinstall Python with "Add Python to PATH" option
   - Or manually copy `python.exe` to `pythonw.exe` in your Python directory

## How do I know if the webhook is running?

### Check Task Status:
```powershell
Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### View Recent Runs:
```powershell
Get-ScheduledTaskInfo -TaskName "BATCH7_AutoCommit_Webhook"
```

### Check Git Log:
```powershell
cd C:\Users\chris\EpsteinEstateBatch7
git log --oneline -10
```

You should see commits every 5 minutes with messages like "Pipeline Update: YYYY-MM-DD HH:MM:SS"

### Check Task History:
1. Open **Task Scheduler**
2. Find `BATCH7_AutoCommit_Webhook`
3. Click **History** tab
4. Look for successful runs (green checkmarks) or errors (red X)

## Can I change the interval?

Yes! Re-run the setup script with a different interval:

```powershell
cd BATCH7
.\setup_webhook_scheduler.ps1 -IntervalMinutes 10
```

This will update the existing task to run every 10 minutes instead of 5.

## How do I temporarily stop the webhook?

### Disable (keeps task, just stops running):
```powershell
Disable-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### Re-enable:
```powershell
Enable-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
```

### Remove completely:
```powershell
Unregister-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook" -Confirm:$false
```

## The webhook stopped working - how do I troubleshoot?

1. **Check if task is enabled:**
   ```powershell
   Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
   ```
   State should be "Ready", not "Disabled"

2. **Check last run result:**
   ```powershell
   (Get-ScheduledTaskInfo -TaskName "BATCH7_AutoCommit_Webhook").LastTaskResult
   ```
   Should be `0` (success). Non-zero means error.

3. **Check Task Scheduler History** for error messages

4. **Test manually:**
   ```powershell
   cd BATCH7
   python auto_commit_webhook.py --once
   ```

5. **Check Python path** - Task might be using wrong Python:
   ```powershell
   $Task = Get-ScheduledTask -TaskName "BATCH7_AutoCommit_Webhook"
   $Task.Actions[0].Execute
   ```

6. **Check git repository** - Make sure you're in a git repo:
   ```powershell
   cd C:\Users\chris\EpsteinEstateBatch7
   git status
   ```

7. **Check network** - Push requires internet connection:
   ```powershell
   git push origin main
   ```

## Can I see what the webhook is doing without checking git?

The webhook runs silently, but you can:

1. **Check the README** - It updates every 5 minutes with latest summary
2. **Check git log** - See commit messages with findings
3. **Check Task Scheduler History** - See when it ran and if it succeeded
4. **Add logging** - Modify `auto_commit_webhook.py` to write to a log file (advanced)

