# Testing Single Instance Enforcement

This guide explains how to test the single instance enforcement feature that prevents multiple instances of the application from running simultaneously.

## Quick Test Methods

### Method 1: Manual Testing (Easiest)

**Step 1:** Start the application normally:
```bash
python main.py
```

**Step 2:** While the first instance is running, try to start a second instance in a new terminal:
```bash
python main.py
```

**Expected Result:**
- The second instance should immediately exit with a message:
  ```
  Another instance of the application is already running.
  Please close the existing instance before starting a new one.
  ```
- The first instance should continue running normally.

**Step 3:** Close the first instance and try starting again - it should work.

---

### Method 2: Run Automated Unit Tests

Run the pytest unit tests:

```bash
# Run all single instance tests
pytest tests/unit/test_single_instance.py -v

# Run a specific test
pytest tests/unit/test_single_instance.py::TestSingleInstance::test_single_instance_detects_existing_instance -v
```

**Expected Result:** All tests should pass ✅

---

### Method 3: Run Manual Test Script

Run the comprehensive manual test script:

```bash
python test_single_instance_manual.py
```

This script will:
- Test basic single instance functionality
- Test context manager usage
- Test lock file cleanup
- Provide detailed output for each test

**Expected Result:** All tests should pass ✅

---

## Detailed Testing Scenarios

### Scenario 1: Normal Operation
1. Start the app → Should start successfully
2. Use the app normally
3. Close the app → Lock should be released

### Scenario 2: Multiple Launch Attempts
1. Start the app (Instance 1)
2. Try to start again (Instance 2) → Should be blocked
3. Try to start again (Instance 3) → Should be blocked
4. Close Instance 1
5. Try to start again → Should succeed

### Scenario 3: Crash Recovery
1. Start the app
2. Force kill the process (Ctrl+C or kill command)
3. Try to start again → Should succeed (lock is released on process termination)

### Scenario 4: Different Terminals/Windows
1. Open Terminal 1 → Start app
2. Open Terminal 2 → Try to start app → Should be blocked
3. Open Terminal 3 → Try to start app → Should be blocked
4. Close app in Terminal 1
5. Try Terminal 2 or 3 → Should succeed

---

## Platform-Specific Testing

### macOS
```bash
# Terminal 1
python main.py

# Terminal 2 (new terminal window)
python main.py
```

### Windows
```cmd
REM Command Prompt 1
python main.py

REM Command Prompt 2 (new window)
python main.py
```

### Linux
```bash
# Terminal 1
python main.py

# Terminal 2 (new terminal)
python main.py
```

---

## Verifying Lock File

The lock file is created at: `data/app.lock`

You can check if it exists:
```bash
# macOS/Linux
ls -la data/app.lock
cat data/app.lock  # Shows the PID of the running instance

# Windows
dir data\app.lock
type data\app.lock
```

**Note:** The lock file should be automatically removed when the app closes normally. If it remains after a crash, it's safe to delete manually (the OS releases the lock when the process dies).

---

## Testing with Different Modes

### Desktop Mode (Default)
```bash
python main.py
```

### Web Mode
```bash
python main.py --web
```

Both modes should enforce single instance.

---

## Troubleshooting

### Issue: Second instance starts anyway
**Possible causes:**
- Lock file permissions issue
- File system doesn't support locking (rare)
- Check logs for errors

**Solution:**
- Check `logs/app.log` for errors
- Verify `data/` directory is writable
- Try running with elevated permissions if needed

### Issue: Lock file remains after app closes
**This is normal** - the file may remain, but the lock is released by the OS when the process terminates. You can safely delete it if needed.

### Issue: Tests fail
**Possible causes:**
- Lock file from previous test run
- Permissions issue

**Solution:**
```bash
# Clean up test lock files
rm -f data/test_instance.lock
rm -f data/app.lock
```

---

## Expected Behavior Summary

✅ **Should Work:**
- First instance starts normally
- Second instance is blocked with clear message
- App works normally after first instance closes
- Lock is released on normal exit
- Lock is released on crash/kill

❌ **Should NOT Happen:**
- Multiple instances running simultaneously
- Silent failures (should show message)
- Lock file preventing restart after crash

---

## Integration with Application

The single instance check happens in `main.py` before the Flet app starts:

```python
single_instance = SingleInstance()
if single_instance.is_already_running():
    print("Another instance is already running.")
    sys.exit(1)
```

This ensures the check happens early, before any UI or services are initialized.

