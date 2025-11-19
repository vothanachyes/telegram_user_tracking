# Windows Build Workflow Guide

This guide explains how to build Windows executables (`.exe` files) from macOS or Linux using GitHub Actions.

## Overview

Since PyInstaller cannot cross-compile (you cannot build a Windows `.exe` from macOS/Linux directly), we use **GitHub Actions** to automatically build Windows executables in the cloud on Windows runners.

## Prerequisites

- A GitHub repository with the project code
- GitHub Actions enabled (enabled by default for public repos)
- Push access to the repository

## Workflow Location

The workflow file is located at:
```
.github/workflows/build-windows.yml
```

## How It Works

1. **Trigger**: The workflow runs when you:
   - Push a version tag (e.g., `v1.0.0`)
   - Manually trigger it from GitHub Actions tab
   - Create a pull request to `main` or `master`

2. **Build Process**:
   - GitHub spins up a Windows runner
   - Installs Python 3.10
   - Installs all dependencies from `requirements.txt`
   - Runs `scripts/build.py` to create the executable
   - Uploads the `.exe` file as a downloadable artifact

3. **Output**: The executable is available as a downloadable artifact for 30 days

## Usage

### Method 1: Manual Trigger (Recommended for Testing)

1. **Push the workflow file** (if not already committed):
   ```bash
   git add .github/workflows/build-windows.yml
   git commit -m "Add GitHub Actions workflow for Windows builds"
   git push
   ```

2. **Trigger the workflow**:
   - Go to your GitHub repository
   - Click on the **"Actions"** tab
   - Select **"Build Windows Executable"** from the workflow list
   - Click **"Run workflow"** button (top right)
   - Select the branch (usually `main` or `master`)
   - Click **"Run workflow"**

3. **Monitor the build**:
   - The workflow will appear in the Actions tab
   - Click on it to see real-time build progress
   - Wait for all steps to complete (usually 5-10 minutes)

4. **Download the executable**:
   - Once the workflow completes successfully, scroll down to the **"Artifacts"** section
   - Click on **"TelegramUserTracking-Windows"** to download the `.exe` file

### Method 2: Automatic Trigger (Version Tags)

For production releases, trigger builds automatically with version tags:

1. **Create and push a version tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **The workflow will automatically start**:
   - Go to the Actions tab to monitor the build
   - Download the executable when complete

3. **Tag naming convention**:
   - Use semantic versioning: `v1.0.0`, `v1.2.3`, `v2.0.0-beta.1`
   - Tags must start with `v` followed by a version number

### Method 3: Pull Request Trigger

The workflow also runs on pull requests to `main` or `master` branches:
- Useful for testing builds before merging
- Artifacts are available for review
- Helps catch build issues early

## Workflow Steps

The workflow performs the following steps:

1. **Checkout code** - Gets the latest code from the repository
2. **Set up Python** - Installs Python 3.10 with pip caching
3. **Install dependencies** - Installs all packages from `requirements.txt` and PyInstaller
4. **Build executable** - Runs `scripts/build.py` to create the Windows executable
5. **Verify executable** - Checks that the `.exe` file was created and shows file size
6. **Upload artifacts** - Makes the executable available for download

## Build Configuration

The build process uses `scripts/build.py`, which:

- Creates a single-file executable (`--onefile`)
- Includes all necessary data files (config, database, services, ui, utils, locales, assets)
- Excludes development files (tests, scripts, sandbox, unused code)
- Adds hidden imports for all required libraries
- Creates Windows version info (if `version_info.txt` exists)
- Uses Windows icon if available (`icons/win/icon.ico` or `assets/icon.ico`)

## Artifacts

After a successful build, two artifacts are created:

1. **TelegramUserTracking-Windows** (30 days retention)
   - Contains: `TelegramUserTracking.exe`
   - This is the main executable you'll distribute

2. **build-logs-windows** (7 days retention)
   - Contains: Build logs and dist folder
   - Useful for debugging failed builds

## Troubleshooting

### Build Fails

**Check the workflow logs**:
1. Go to Actions tab → Click on failed workflow
2. Expand each step to see error messages
3. Common issues:
   - Missing dependencies in `requirements.txt`
   - Syntax errors in `scripts/build.py`
   - Missing required files (icons, config files)
   - PyInstaller errors (missing hidden imports)

**Common Solutions**:
- Ensure all dependencies are in `requirements.txt`
- Check that `scripts/build.py` runs successfully locally (on Windows if possible)
- Verify all data files exist (config, database, services, ui, utils)
- Add missing hidden imports to `scripts/build.py`

### Executable Not Found

If the verification step fails:
- Check the build logs for PyInstaller errors
- Verify `main.py` exists in the project root
- Ensure the build script is in `scripts/build.py`
- Check that PyInstaller completed successfully

### Large Executable Size

The executable includes:
- Python interpreter
- All dependencies (Flet, Pyrogram, Firebase, etc.)
- All application code and data files

**Typical sizes**: 50-150 MB (depending on dependencies)

**To reduce size**:
- Remove unused dependencies from `requirements.txt`
- Use `--exclude-module` in `scripts/build.py` for unused libraries
- Consider using `--onedir` instead of `--onefile` (creates a folder instead)

### Version Info Not Working

The workflow automatically creates `version_info.txt` on Windows. If version info is missing:
- Check that `create_version_info()` function runs in `scripts/build.py`
- Verify the file is created before PyInstaller runs
- Ensure PyInstaller can find `version_info.txt` in the project root

## Local Testing

Before pushing to GitHub, test the build script locally:

**On Windows**:
```bash
python scripts/build.py
```

**On macOS/Linux** (won't create .exe, but tests the script):
```bash
python scripts/build.py
# Will fail at PyInstaller step, but validates the script logic
```

## Best Practices

1. **Test locally first**: Run `scripts/build.py` on Windows before pushing
2. **Use version tags**: Tag releases for automatic builds
3. **Monitor builds**: Check Actions tab regularly for failed builds
4. **Keep dependencies updated**: Update `requirements.txt` with exact versions
5. **Document changes**: Update this guide if build process changes
6. **Test the executable**: Always test the downloaded `.exe` before distribution

## Workflow Customization

To modify the workflow, edit `.github/workflows/build-windows.yml`:

**Change Python version**:
```yaml
python-version: '3.11'  # Change from '3.10'
```

**Add build steps**:
```yaml
- name: Custom step
  run: |
    echo "Your custom command here"
```

**Modify triggers**:
```yaml
on:
  push:
    branches:
      - main
      - develop  # Add more branches
```

**Change artifact retention**:
```yaml
retention-days: 60  # Change from 30
```

## Security Notes

- **Never commit secrets**: The workflow runs in a clean environment
- **Artifacts are public**: If repository is public, artifacts are downloadable by anyone
- **Use private repos**: For private builds, ensure repository is private
- **Review dependencies**: All packages in `requirements.txt` are installed

## Related Files

- `scripts/build.py` - Build script that creates the executable
- `requirements.txt` - Python dependencies
- `main.py` - Application entry point
- `.github/workflows/build-windows.yml` - GitHub Actions workflow

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Python Packaging Guide](https://packaging.python.org/)

## Support

For issues with the build workflow:
1. Check the workflow logs in GitHub Actions
2. Review this documentation
3. Test the build script locally on Windows
4. Check PyInstaller documentation for specific errors

## Version History

- **v1.0.0** - Initial workflow setup with Windows build support

