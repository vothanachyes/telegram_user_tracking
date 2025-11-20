# Code Protection Guide

## Overview

The build system includes three layers of code protection to prevent reverse engineering and protect your intellectual property:

1. **PyArmor Obfuscation** - Transforms readable Python code into obfuscated bytecode
2. **Bytecode Encryption** - Encrypts Python bytecode using PyInstaller's `--key` option
3. **Source File Removal** - Removes `.py` source files from the final bundle

## 🔒 Protection Layers

### Layer 1: PyArmor Obfuscation

**What it does:**
- Obfuscates variable names, function names, and control flow
- Encrypts string literals and constants
- Makes decompilation extremely difficult
- Works seamlessly with PyInstaller

**Status:** ✅ Enabled by default

**Requirements:**
- PyArmor must be installed: `pip install pyarmor`
- Free version provides basic obfuscation
- Commercial license required for advanced features (machine binding, expiration, etc.)

**How it works:**
1. Before building, PyArmor processes all production code
2. Creates obfuscated version in `obfuscated_temp/` directory
3. PyInstaller bundles the obfuscated code instead of original
4. Temporary directory is cleaned up after build

**What gets obfuscated:**
- `main.py`
- `config/` directory
- `database/` directory
- `services/` directory
- `ui/` directory
- `utils/` directory

**What doesn't get obfuscated:**
- Non-Python files (JSON, YAML, etc.) are copied as-is
- Third-party dependencies (handled by PyInstaller)
- Test files and development scripts (excluded from build)

### Layer 2: Bytecode Encryption

**What it does:**
- Encrypts Python bytecode using AES encryption
- Requires decryption key at runtime
- Adds an extra layer of protection even if obfuscation is bypassed

**Status:** ✅ Enabled by default

**Encryption Key:**
- Auto-generated on first build
- Stored in `.build_key` file (root directory)
- **IMPORTANT:** Keep this file secure and never commit it to Git
- Same key is reused for consistent builds
- If key is lost, you must regenerate (old builds won't work)

**How it works:**
- PyInstaller uses `--key` option with your encryption key
- Bytecode is encrypted before being bundled
- Decryption happens at runtime automatically

### Layer 3: Source File Removal

**What it does:**
- Removes all `.py` source files from the final bundle
- Keeps only bytecode (`.pyc`) files
- Prevents casual inspection of source code

**Status:** ✅ Enabled by default

**What gets removed:**
- All `.py` files in the bundle
- Exception: `__init__.py` files are kept (required by Python packages)

**What stays:**
- Compiled bytecode (`.pyc` files)
- Non-Python files (JSON, images, etc.)
- Required `__init__.py` files

## 📋 Configuration

### Build Script Settings

Edit `scripts/build.py` to configure protection:

```python
# Code protection settings
USE_PYARMOR = True              # Enable/disable PyArmor obfuscation
USE_BYTECODE_ENCRYPTION = True  # Enable/disable --key encryption
REMOVE_SOURCE_FILES = True      # Enable/disable .py file removal
```

### Disabling Protection

To disable any protection layer, set the corresponding flag to `False`:

```python
USE_PYARMOR = False  # Skip obfuscation (faster builds)
```

**Note:** Even if PyArmor fails or is disabled, the other two layers still work.

## 🚀 Usage

### Prerequisites

1. **Install PyArmor:**
   ```bash
   pip install pyarmor
   ```

2. **Verify installation:**
   ```bash
   pyarmor --version
   ```

### Building with Protection

1. **Run the build script:**
   ```bash
   python scripts/build.py
   ```

2. **Build process:**
   - Step 1: Obfuscates code with PyArmor
   - Step 2: Builds executable with PyInstaller (encrypted)
   - Step 3: Removes source files from bundle
   - Cleanup: Removes temporary files

3. **Check protection status:**
   The build script shows protection status at the end:
   ```
   🔒 Code Protection Status:
     ✅ PyArmor obfuscation: ENABLED
     ✅ Bytecode encryption: ENABLED
     ✅ Source file removal: ENABLED
   ```

## ⚠️ Important Notes

### PyArmor License

**Free Version:**
- ✅ Basic obfuscation
- ✅ Works with PyInstaller
- ✅ String encryption
- ❌ No machine binding
- ❌ No expiration dates
- ❌ No license management

**Commercial License:**
- ✅ All free features
- ✅ Machine binding (lock to specific hardware)
- ✅ Expiration dates (trial versions)
- ✅ License management
- 💰 Requires purchase

**Recommendation:** Start with free version. Upgrade if you need advanced features.

### Encryption Key Security

**CRITICAL:** The `.build_key` file contains your encryption key.

**DO:**
- ✅ Keep `.build_key` secure and private
- ✅ Back up `.build_key` in a secure location
- ✅ Use the same key for consistent builds
- ✅ Add `.build_key` to `.gitignore` (already done)

**DON'T:**
- ❌ Commit `.build_key` to Git
- ❌ Share `.build_key` publicly
- ❌ Delete `.build_key` without backup
- ❌ Use different keys for the same version

**If key is lost:**
- Old builds will continue to work
- New builds will use a new key
- You cannot decrypt old builds with a new key

### Build Performance

**Impact of protection:**
- **PyArmor:** Adds 1-3 minutes to build time
- **Encryption:** Minimal impact (< 10 seconds)
- **File removal:** Minimal impact (< 5 seconds)

**Total overhead:** ~2-4 minutes per build

### Compatibility

**Tested platforms:**
- ✅ macOS (Darwin)
- ✅ Windows
- ✅ Linux

**Python versions:**
- ✅ Python 3.10+
- ✅ Python 3.13 (tested)

**Dependencies:**
- All standard dependencies work with obfuscation
- Third-party packages are not obfuscated (handled by PyInstaller)

## 🔧 Troubleshooting

### PyArmor Not Installed

**Error:**
```
❌ PyArmor is not installed!
   Install it with: pip install pyarmor
```

**Solution:**
```bash
pip install pyarmor
```

**Fallback:** Build continues without obfuscation (encryption and file removal still work)

### PyArmor Obfuscation Fails

**Error:**
```
❌ PyArmor obfuscation failed: ...
   Falling back to non-obfuscated build...
```

**Possible causes:**
1. PyArmor version incompatible
2. Syntax errors in code
3. Missing dependencies

**Solutions:**
1. Update PyArmor: `pip install --upgrade pyarmor`
2. Fix syntax errors in your code
3. Check PyArmor logs for specific errors
4. Build will continue with other protections enabled

### Encryption Key Issues

**Problem:** Build fails with encryption key error

**Solution:**
1. Delete `.build_key` file
2. Run build again (new key will be generated)
3. Note: Old builds won't work with new key

**Problem:** Want to use a specific key

**Solution:**
1. Generate a key: `python -c "import secrets; print(secrets.token_hex(16))"`
2. Save it to `.build_key` file
3. Run build

### Source Files Still Visible

**Problem:** `.py` files still in bundle after build

**Possible causes:**
1. `REMOVE_SOURCE_FILES = False`
2. Build failed before removal step
3. Files in unexpected location

**Solutions:**
1. Check `REMOVE_SOURCE_FILES` flag in `build.py`
2. Verify build completed successfully
3. Manually check bundle structure

### Build Size Increased

**Expected:** Protected builds are slightly larger due to:
- Obfuscation overhead
- Encryption metadata
- PyArmor runtime

**Typical increase:** 5-15 MB

## 📊 Protection Comparison

| Method | Protection Level | Build Time | File Size | Cost |
|--------|-----------------|------------|-----------|------|
| **No Protection** | ⚠️ Low | Fast | Small | Free |
| **File Removal Only** | ⚠️ Low-Medium | Fast | Small | Free |
| **Encryption Only** | ✅ Medium | Fast | Small | Free |
| **PyArmor Only** | ✅ Medium-High | Medium | Medium | Free/Paid |
| **All Three Layers** | ✅✅ High | Medium | Medium | Free/Paid |

## 🎯 Best Practices

### For Development

1. **Disable protection during development:**
   ```python
   USE_PYARMOR = False
   USE_BYTECODE_ENCRYPTION = False
   REMOVE_SOURCE_FILES = False
   ```
   - Faster builds
   - Easier debugging
   - No obfuscation overhead

### For Production

1. **Enable all protections:**
   ```python
   USE_PYARMOR = True
   USE_BYTECODE_ENCRYPTION = True
   REMOVE_SOURCE_FILES = True
   ```
   - Maximum security
   - Protects intellectual property
   - Prevents reverse engineering

2. **Test protected builds:**
   - Always test the protected build before release
   - Some edge cases may behave differently
   - Verify all features work correctly

3. **Backup encryption key:**
   - Store `.build_key` in secure location
   - Use version control for key (private repo)
   - Document key location for team members

### For Distribution

1. **Version consistency:**
   - Use same encryption key for same version
   - Different versions can use different keys
   - Document which key was used for which version

2. **Build verification:**
   - Check protection status after build
   - Verify source files are removed
   - Test executable functionality

## 🔍 Verification

### Check Protection Status

After build, look for this output:
```
🔒 Code Protection Status:
  ✅ PyArmor obfuscation: ENABLED
  ✅ Bytecode encryption: ENABLED
  ✅ Source file removal: ENABLED
```

### Verify Source Files Removed

**macOS:**
```bash
find dist/TelegramUserTracking.app/Contents/Resources -name "*.py" -not -name "__init__.py"
```

**Windows:**
```powershell
Get-ChildItem -Path dist\TelegramUserTracking -Recurse -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" }
```

**Expected:** No results (or only `__init__.py` files)

### Verify Obfuscation

1. Extract bundle contents
2. Look for obfuscated code patterns:
   - Random variable names (e.g., `x1`, `a2b3`)
   - Encrypted strings
   - Obfuscated control flow

## 📚 Additional Resources

- **PyArmor Documentation:** https://pyarmor.readthedocs.io/
- **PyInstaller Documentation:** https://pyinstaller.org/
- **PyArmor License:** https://pyarmor.readthedocs.io/en/latest/licenses.html

## 🆘 Support

If you encounter issues:

1. **Check build logs** for specific error messages
2. **Verify PyArmor installation:** `pyarmor --version`
3. **Test without protection** to isolate issues
4. **Check Python version compatibility**
5. **Review PyArmor documentation** for specific errors

## 📝 Summary

The three-layer protection system provides strong security for your Python application:

1. **PyArmor** obfuscates code to make reverse engineering difficult
2. **Encryption** adds an extra layer of bytecode protection
3. **File removal** prevents casual source code inspection

All three layers work together to provide maximum protection while maintaining application functionality. The system is designed to fail gracefully - if one layer fails, others continue to work.

**Remember:**
- Keep `.build_key` secure
- Test protected builds before release
- Back up encryption keys
- Use all three layers for maximum security

