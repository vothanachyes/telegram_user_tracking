"""
Build script for creating executable with PyInstaller.
Includes code protection: PyArmor obfuscation and source file removal.
Note: Bytecode encryption (--key) was removed in PyInstaller v6.0+
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# Import app metadata
try:
    from utils.constants import APP_NAME, APP_VERSION, DEVELOPER_NAME
except ImportError:
    # Fallback if constants not available
    APP_NAME = "Telegram User Tracking"
    APP_VERSION = "1.0.0"
    DEVELOPER_NAME = "Vothana CHY"

# Get project root (parent of scripts/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Code protection settings
USE_PYARMOR = True  # Set to False to disable PyArmor obfuscation
USE_BYTECODE_ENCRYPTION = False  # DISABLED: PyInstaller removed --key option in v6.0+
REMOVE_SOURCE_FILES = True  # Remove .py files after build
USE_INSTALLER = True  # Set to False to disable Inno Setup installer creation (Windows only)

# Obfuscation temporary directory
OBFUSCATED_DIR = PROJECT_ROOT / 'obfuscated_temp'


def obfuscate_code() -> bool:
    """
    Obfuscate Python code using PyArmor.
    
    Returns:
        True if obfuscation succeeded, False otherwise.
    """
    if not USE_PYARMOR:
        print("PyArmor obfuscation is disabled")
        return True
    
    print("\n" + "=" * 60)
    print("Step 1: Obfuscating code with PyArmor...")
    print("=" * 60)
    
    # Check if PyArmor is installed
    try:
        result = subprocess.run(
            ['pyarmor', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"PyArmor version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyArmor is not installed!")
        print("   Install it with: pip install pyarmor")
        print("   Or set USE_PYARMOR = False to skip obfuscation")
        return False
    
    # Clean up previous obfuscation
    if OBFUSCATED_DIR.exists():
        print(f"  Removing previous obfuscation: {OBFUSCATED_DIR}")
        shutil.rmtree(OBFUSCATED_DIR)
    
    # Directories to obfuscate (production code only)
    code_dirs = ['config', 'database', 'services', 'ui', 'utils']
    
    print("\nObfuscating code directories and files...")
    
    try:
        # Obfuscate main.py first
        print("  Obfuscating main.py...")
        pyarmor_cmd = [
            'pyarmor', 'gen',
            '--output', str(OBFUSCATED_DIR),
            str(PROJECT_ROOT / 'main.py'),
        ]
        
        result = subprocess.run(pyarmor_cmd, check=True, cwd=PROJECT_ROOT)
        
        # Obfuscate each directory
        for dir_name in code_dirs:
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                print(f"  Obfuscating {dir_name}/...")
                pyarmor_cmd = [
                    'pyarmor', 'gen',
                    '--recursive',
                    '--output', str(OBFUSCATED_DIR / dir_name),
                    str(dir_path),
                ]
                result = subprocess.run(pyarmor_cmd, check=True, cwd=PROJECT_ROOT)
        
        # Copy non-Python files (config JSON, etc.) to obfuscated directory
        print("  Copying non-Python files...")
        for dir_name in code_dirs:
            src_dir = PROJECT_ROOT / dir_name
            dst_dir = OBFUSCATED_DIR / dir_name
            if src_dir.exists() and dst_dir.exists():
                # Copy JSON, YAML, and other config files
                for ext in ['*.json', '*.yaml', '*.yml', '*.txt', '*.md']:
                    for file in src_dir.rglob(ext):
                        rel_path = file.relative_to(src_dir)
                        dst_file = dst_dir / rel_path
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file, dst_file)
        
        # Flatten nested structure created by PyArmor
        # PyArmor creates dir/dir/ structure, but we need dir/ for imports
        print("  Flattening nested directory structure...")
        for dir_name in code_dirs:
            nested_dir = OBFUSCATED_DIR / dir_name / dir_name
            target_dir = OBFUSCATED_DIR / dir_name
            if nested_dir.exists() and nested_dir.is_dir():
                # Move all files from nested_dir to target_dir
                for item in nested_dir.iterdir():
                    target_item = target_dir / item.name
                    if target_item.exists():
                        if target_item.is_dir():
                            shutil.rmtree(target_item)
                        else:
                            target_item.unlink()
                    shutil.move(str(item), str(target_item))
                # Remove the now-empty nested directory
                try:
                    nested_dir.rmdir()
                except OSError:
                    pass  # Directory might not be empty if there are subdirs
        
        print("✅ Code obfuscation completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PyArmor obfuscation failed: {e}")
        print("   Falling back to non-obfuscated build...")
        return False


def find_inno_setup_compiler() -> Path:
    """
    Find Inno Setup Compiler (iscc.exe) in common installation locations.
    
    Returns:
        Path to iscc.exe if found, None otherwise.
    """
    # Common installation paths for Inno Setup
    common_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/iscc.exe"),
        Path("C:/Program Files/Inno Setup 6/iscc.exe"),
        Path("C:/Program Files (x86)/Inno Setup 5/iscc.exe"),
        Path("C:/Program Files/Inno Setup 5/iscc.exe"),
    ]
    
    # Check if iscc is in PATH
    try:
        result = subprocess.run(
            ['iscc'],
            capture_output=True,
            text=True,
            check=False
        )
        # If command exists (even with error), return 'iscc' as it's in PATH
        return Path('iscc')
    except FileNotFoundError:
        pass
    
    # Check common installation paths
    for path in common_paths:
        if path.exists():
            return path
    
    return None


def create_installer_script(
    exe_path: Path,
    output_dir: Path,
    app_name: str,
    app_version: str,
    developer_name: str,
    github_repo: str = ""
) -> Path:
    """
    Create Inno Setup script (.iss) file with application metadata.
    
    Args:
        exe_path: Path to the built executable
        output_dir: Directory where installer will be created
        app_name: Application name
        app_version: Application version
        developer_name: Developer/Publisher name
        github_repo: GitHub repository (optional)
    
    Returns:
        Path to the created .iss file
    """
    # Load template
    template_path = PROJECT_ROOT / 'scripts' / 'TelegramUserTracking.iss'
    if not template_path.exists():
        raise FileNotFoundError(f"Inno Setup template not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Generate AppId from app name (for uninstaller tracking)
    # Use a stable AppId format based on app name
    app_id = app_name.replace(' ', '').replace('-', '')
    
    # Determine icon path
    icon_path = PROJECT_ROOT / 'assets' / 'icons' / 'win' / 'icon.ico'
    if not icon_path.exists():
        icon_path = PROJECT_ROOT / 'assets' / 'icon.ico'
    
    # Generate installer output filename
    version_clean = app_version.replace('.', '_')
    output_base_file = f"TelegramUserTracking-Setup-v{version_clean}.exe"
    
    # Replace placeholders in template
    replacements = {
        '{APP_NAME}': app_name,
        '{APP_VERSION}': app_version,
        '{DEVELOPER_NAME}': developer_name,
        '{GITHUB_REPO}': github_repo or 'telegram-user-tracking',
        '{APP_ID}': app_id,
        '{OUTPUT_DIR}': str(output_dir).replace('\\', '\\\\'),
        '{OUTPUT_BASE_FILE}': output_base_file,
        '{ICON_FILE}': str(icon_path).replace('\\', '\\\\') if icon_path.exists() else '',
        '{SOURCE_EXE}': str(exe_path).replace('\\', '\\\\'),
    }
    
    script_content = template
    for placeholder, value in replacements.items():
        script_content = script_content.replace(placeholder, value)
    
    # Handle empty icon file (remove SetupIconFile line if no icon)
    if not icon_path.exists():
        script_content = script_content.replace('SetupIconFile={#ICON_FILE}\n', '; SetupIconFile={#ICON_FILE}\n')
    
    # Write generated script
    iss_file = PROJECT_ROOT / 'scripts' / 'TelegramUserTracking_generated.iss'
    with open(iss_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return iss_file


def build_installer(
    exe_path: Path,
    app_name: str,
    app_version: str,
    developer_name: str
) -> Path:
    """
    Build Windows installer using Inno Setup.
    
    Args:
        exe_path: Path to the built executable
        app_name: Application name
        app_version: Application version
        developer_name: Developer/Publisher name
    
    Returns:
        Path to the created installer .exe file, or None if failed
    """
    if not USE_INSTALLER:
        print("Inno Setup installer creation is disabled")
        return None
    
    print("\n" + "=" * 60)
    print("Step 3: Creating Windows Installer with Inno Setup...")
    print("=" * 60)
    
    # Find Inno Setup Compiler
    iscc_path = find_inno_setup_compiler()
    if not iscc_path:
        print("⚠️  Inno Setup Compiler (iscc.exe) not found!")
        print("   Install Inno Setup from: https://jrsoftware.org/isinfo.php")
        print("   Or set USE_INSTALLER = False to skip installer creation")
        return None
    
    print(f"  Found Inno Setup Compiler: {iscc_path}")
    
    # Check if executable exists
    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
        return None
    
    # Create output directory
    output_dir = PROJECT_ROOT / 'dist'
    output_dir.mkdir(exist_ok=True)
    
    # Generate installer script
    try:
        iss_file = create_installer_script(
            exe_path=exe_path,
            output_dir=output_dir,
            app_name=app_name,
            app_version=app_version,
            developer_name=developer_name
        )
        print(f"  Generated installer script: {iss_file.name}")
    except Exception as e:
        print(f"❌ Failed to create installer script: {e}")
        return None
    
    # Compile installer
    try:
        print("  Compiling installer...")
        cmd = [str(iscc_path), str(iss_file)]
        result = subprocess.run(
            cmd,
            check=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        # Clean up generated script
        if iss_file.exists():
            iss_file.unlink()
        
        # Find the created installer
        version_clean = app_version.replace('.', '_')
        installer_name = f"TelegramUserTracking-Setup-v{version_clean}.exe"
        installer_path = output_dir / installer_name
        
        if installer_path.exists():
            installer_size = installer_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Installer created successfully: {installer_path.name}")
            print(f"   Size: {installer_size:.2f} MB")
            return installer_path
        else:
            print(f"⚠️  Installer compilation completed but file not found: {installer_name}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Inno Setup compilation failed: {e}")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        # Clean up generated script
        if iss_file.exists():
            iss_file.unlink()
        return None
    except Exception as e:
        print(f"❌ Unexpected error during installer creation: {e}")
        # Clean up generated script
        if iss_file.exists():
            iss_file.unlink()
        return None


def build_executable():
    """Build executable for current platform with code protection."""
    
    print("=" * 60)
    print("Telegram User Tracking - Build Script (Protected)")
    print("=" * 60)
    
    # Get platform info
    system = platform.system()
    print(f"\nBuilding for: {system}")
    
    # Change to project root directory for build
    os.chdir(PROJECT_ROOT)
    
    # Clean up previous build artifacts
    print("\nCleaning up previous build artifacts...")
    
    # Delete dist directory if it exists
    dist_dir = PROJECT_ROOT / 'dist'
    if dist_dir.exists():
        print(f"  Removing {dist_dir}")
        shutil.rmtree(dist_dir)
    
    # Delete build directory if it exists
    build_dir = PROJECT_ROOT / 'build'
    if build_dir.exists():
        print(f"  Removing {build_dir}")
        shutil.rmtree(build_dir)
    
    # Delete spec file if it exists
    spec_file = PROJECT_ROOT / 'TelegramUserTracking.spec'
    if spec_file.exists():
        print(f"  Removing {spec_file.name}")
        spec_file.unlink()
    
    # Step 1: Obfuscate code (if enabled)
    obfuscation_success = obfuscate_code()
    
    # Determine source directory (obfuscated or original)
    if USE_PYARMOR and obfuscation_success and OBFUSCATED_DIR.exists():
        source_dir = OBFUSCATED_DIR
        main_file = OBFUSCATED_DIR / 'main.py'
        print(f"\nUsing obfuscated code from: {source_dir}")
    else:
        source_dir = PROJECT_ROOT
        main_file = PROJECT_ROOT / 'main.py'
        print(f"\nUsing original code from: {source_dir}")
    
    if not main_file.exists():
        print(f"❌ Main file not found: {main_file}")
        return 1
    
    # Step 2: Build with PyInstaller
    print("\n" + "=" * 60)
    print("Step 2: Building executable with PyInstaller...")
    print("=" * 60)
    
    # Use --onedir for macOS (required for .app bundles), --onefile for others
    build_mode = '--onedir' if system == 'Darwin' else '--onefile'
    cmd = [
        'pyinstaller',
        '--name=TelegramUserTracking',
        build_mode,
        '--windowed',
        '--clean',
        '--noconfirm',  # Skip confirmation prompts
    ]
    
    # Bytecode encryption removed: PyInstaller v6.0+ no longer supports --key option
    # Use PyArmor obfuscation instead for code protection
    if USE_BYTECODE_ENCRYPTION:
        print("  ⚠️  Bytecode encryption is disabled (not supported in PyInstaller v6.0+)")
        print("     Use PyArmor obfuscation for code protection instead")
    
    # Use obfuscated main.py or original
    cmd.append(str(main_file))
    
    # Add icon if available
    icon_added = False
    if system == 'Windows':
        win_icon = PROJECT_ROOT / 'assets' / 'icons' / 'win' / 'icon.ico'
        if win_icon.exists():
            cmd.extend(['--icon=assets/icons/win/icon.ico'])
            icon_added = True
            print(f"Using icon: {win_icon}")
    elif system == 'Darwin':  # macOS
        mac_icon = PROJECT_ROOT / 'assets' / 'icons' / 'mac' / 'icon.icns'
        if mac_icon.exists():
            cmd.extend(['--icon=assets/icons/mac/icon.icns'])
            icon_added = True
            print(f"Using icon: {mac_icon}")
    
    if not icon_added:
        print("⚠️  No icon found - building without icon")
    
    # Add data files (from original project, not obfuscated)
    # Note: Config, assets, etc. should come from original project
    data_files = [
        '--add-data=config:config',
        '--add-data=database:database',
        '--add-data=services:services',
        '--add-data=ui:ui',
        '--add-data=utils:utils',
    ]
    
    # Add Python paths for importable modules
    python_paths = []
    
    # If using obfuscated code, we need to adjust paths
    if USE_PYARMOR and obfuscation_success and OBFUSCATED_DIR.exists():
        # For obfuscated builds, add obfuscated directories to Python path
        # This makes them importable as Python modules
        python_paths = [
            '--paths', str(OBFUSCATED_DIR),
        ]
        # Also add as data files for non-Python files (JSON, etc.)
        data_files = [
            f'--add-data={OBFUSCATED_DIR}/config:config',
            f'--add-data={OBFUSCATED_DIR}/database:database',
            f'--add-data={OBFUSCATED_DIR}/services:services',
            f'--add-data={OBFUSCATED_DIR}/ui:ui',
            f'--add-data={OBFUSCATED_DIR}/utils:utils',
        ]
    else:
        # For non-obfuscated builds, add project root to Python path
        python_paths = [
            '--paths', str(PROJECT_ROOT),
        ]
    
    # Add locales if they exist
    if (PROJECT_ROOT / 'locales').exists():
        data_files.append('--add-data=locales:locales')
    
    # Add assets if they exist
    if (PROJECT_ROOT / 'assets').exists():
        data_files.append('--add-data=assets:assets')
    
    # Note: Firebase credentials are NO LONGER bundled (security improvement)
    # Desktop app uses REST API with ID tokens - no Admin SDK credentials needed
    config_dir = PROJECT_ROOT / 'config'
    firebase_creds = list(config_dir.glob('*.json'))
    if firebase_creds:
        print(f"\n⚠️  Found Firebase credentials file(s) in config/ (will be EXCLUDED from build):")
        for cred_file in firebase_creds:
            print(f"  - {cred_file.name} (excluded for security)")
        print("   Desktop app uses REST API - credentials only needed for deployment scripts")
    
    # Add Python paths first (for importable modules)
    cmd.extend(python_paths)
    # Then add data files
    cmd.extend(data_files)
    
    # Exclude unrelated code from build
    exclude_modules = [
        'tests', 'z_sanbox', 'unused', 'scripts', 'admin',
        'pytest', 'pytest_', 'test_single_instance_manual',
        'decrypt_pin', 'icon_maker',
        'firebase_admin',  # Admin SDK not needed in desktop app (uses REST API)
    ]
    
    print("\nExcluding from build:")
    for module in exclude_modules:
        print(f"  - {module}")
        cmd.extend(['--exclude-module', module])
    
    # Hidden imports
    hidden_imports = [
        'flet', 'telethon', 'pandas',
        'xlsxwriter', 'reportlab', 'PIL', 'dotenv', 'cryptography',
        'qrcode',  # QR code generation
        # Note: firebase_admin excluded - desktop app uses REST API, not Admin SDK
        # UI components
        'ui.components.tag_autocomplete',
        # Utils modules (required for PyArmor obfuscated builds)
        'utils',
        'utils.logging_config',
        'utils.constants',
        'utils.credential_storage',
        'utils.db_commands',
        'utils.group_parser',
        'utils.helpers',
        'utils.pin_attempt_manager',
        'utils.pin_validator',
        'utils.rich_content_renderer',
        'utils.single_instance',
        'utils.tag_extractor',
        'utils.user_pin_encryption',
        'utils.validators',
        'utils.version_utils',
        'utils.windows_auth',
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Collect all submodules for packages with many nested modules
    cmd.extend(['--collect-submodules', 'cryptography'])
    cmd.extend(['--collect-submodules', 'reportlab'])
    
    # Add runtime hook for obfuscated imports (if using PyArmor)
    if USE_PYARMOR and obfuscation_success:
        runtime_hook = PROJECT_ROOT / 'scripts' / 'pyi_rth_obfuscated_imports.py'
        if runtime_hook.exists():
            cmd.extend(['--runtime-hook', str(runtime_hook)])
            print(f"  Using runtime hook: {runtime_hook.name}")
    
    # Build info
    if system == 'Windows':
        cmd.append('--version-file=version_info.txt')
    
    print("\nRunning PyInstaller...")
    print(" ".join(cmd))
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        
        # Step 3: Remove source files (Option 3)
        # NOTE: Skip this step when using PyArmor - obfuscated files are needed at runtime
        if REMOVE_SOURCE_FILES and not (USE_PYARMOR and obfuscation_success):
            print("\n" + "=" * 60)
            print("Step 3: Removing source files from bundle...")
            print("=" * 60)
            
            resources_dir = None
            if system == 'Darwin':
                resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking.app' / 'Contents' / 'Resources'
            elif system == 'Windows':
                # For onefile, files are embedded in exe
                # For onedir, files are in dist/TelegramUserTracking/
                if build_mode == '--onedir':
                    resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking'
            else:
                resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking'
            
            if resources_dir and resources_dir.exists():
                removed_count = 0
                for py_file in resources_dir.rglob('*.py'):
                    # Skip __init__.py files (some packages need them)
                    if py_file.name == '__init__.py':
                        continue
                    try:
                        py_file.unlink()
                        removed_count += 1
                    except Exception as e:
                        print(f"  Warning: Could not remove {py_file}: {e}")
                print(f"  ✅ Removed {removed_count} source files")
        elif REMOVE_SOURCE_FILES and USE_PYARMOR and obfuscation_success:
            print("\n" + "=" * 60)
            print("Step 3: Skipping source file removal (PyArmor obfuscated files needed at runtime)")
            print("=" * 60)
            print("  ℹ️  Obfuscated .py files are kept in bundle (required for execution)")
            print("  ℹ️  Files are already protected by PyArmor obfuscation")
        
        # Remove Firebase credentials JSON files (security - no Admin SDK in desktop app)
        # This applies to both obfuscated and non-obfuscated builds
        resources_dir = None
        if system == 'Darwin':
            resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking.app' / 'Contents' / 'Resources'
        elif system == 'Windows':
            if build_mode == '--onedir':
                resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking'
            # For --onefile on Windows, files are embedded in exe, so no resources_dir
        else:
            resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking'
        
        if resources_dir and resources_dir.exists():
            config_dir = resources_dir / 'config'
            if config_dir.exists():
                creds_removed = 0
                for cred_file in config_dir.glob('*.json'):
                    # Check if it's a Firebase credentials file
                    if 'firebase' in cred_file.name.lower() or 'fbsvc' in cred_file.name.lower():
                        try:
                            cred_file.unlink()
                            creds_removed += 1
                            print(f"  ✅ Removed Firebase credentials: {cred_file.name}")
                        except Exception as e:
                            print(f"  Warning: Could not remove {cred_file}: {e}")
                if creds_removed > 0:
                    print(f"  ✅ Removed {creds_removed} Firebase credential file(s) (security improvement)")
        else:
            if resources_dir:
                print(f"  ⚠️  Resources directory not found: {resources_dir}")
        
        # Clean up obfuscated temp directory
        if OBFUSCATED_DIR.exists():
            print(f"\nCleaning up obfuscation temp directory...")
            shutil.rmtree(OBFUSCATED_DIR)
        
        # Step 4: Fix Info.plist for macOS (prevent duplicate dock icons)
        if system == 'Darwin':
            print("\n" + "=" * 60)
            print("Step 4: Updating Info.plist for macOS...")
            print("=" * 60)
            info_plist = PROJECT_ROOT / 'dist' / 'TelegramUserTracking.app' / 'Contents' / 'Info.plist'
            if info_plist.exists():
                try:
                    import plistlib
                    # Read existing plist
                    with open(info_plist, 'rb') as f:
                        plist = plistlib.load(f)
                    
                    # Set proper bundle identifier (reverse domain format)
                    plist['CFBundleIdentifier'] = 'com.telegramusertracking.app'
                    
                    # Add LSApplicationCategoryType to prevent duplicate icons
                    plist['LSApplicationCategoryType'] = 'public.app-category.utilities'
                    
                    # Add LSUIElement to prevent showing in dock (if you want background app)
                    # But we want it in dock, so don't set this
                    # plist['LSUIElement'] = False
                    
                    # Add NSHighResolutionCapable if not present
                    if 'NSHighResolutionCapable' not in plist:
                        plist['NSHighResolutionCapable'] = True
                    
                    # Write back
                    with open(info_plist, 'wb') as f:
                        plistlib.dump(plist, f)
                    
                    print("  ✅ Updated Info.plist with proper bundle identifier")
                except Exception as e:
                    print(f"  ⚠️  Could not update Info.plist: {e}")
        
        # Step 5: Create Windows Installer (Windows only)
        installer_path = None
        if system == 'Windows' and USE_INSTALLER:
            exe_path = PROJECT_ROOT / 'dist' / 'TelegramUserTracking.exe'
            if exe_path.exists():
                installer_path = build_installer(
                    exe_path=exe_path,
                    app_name=APP_NAME,
                    app_version=APP_VERSION,
                    developer_name=DEVELOPER_NAME
                )
            else:
                print("\n⚠️  Executable not found, skipping installer creation")
        
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        
        # Show protection status
        print("\n🔒 Code Protection Status:")
        if USE_PYARMOR and obfuscation_success:
            print("  ✅ PyArmor obfuscation: ENABLED")
        else:
            print("  ⚠️  PyArmor obfuscation: DISABLED or FAILED")
        
        if USE_BYTECODE_ENCRYPTION:
            print("  ⚠️  Bytecode encryption: NOT SUPPORTED (PyInstaller v6.0+)")
        else:
            print("  ⚠️  Bytecode encryption: DISABLED (not supported in PyInstaller v6.0+)")
        
        if REMOVE_SOURCE_FILES:
            print("  ✅ Source file removal: ENABLED")
        else:
            print("  ⚠️  Source file removal: DISABLED")
        
        # Show correct output location based on platform
        if system == 'Windows':
            output_path = "dist/TelegramUserTracking.exe"
            if installer_path:
                installer_size = installer_path.stat().st_size / (1024 * 1024)  # MB
                print(f"\n📦 Executable location: {output_path}")
                print(f"📦 Installer location: {installer_path.name} ({installer_size:.2f} MB)")
            else:
                print(f"\n📦 Executable location: {output_path}")
        elif system == 'Darwin':
            output_path = "dist/TelegramUserTracking.app"
            print(f"\n📦 Executable location: {output_path}")
        else:
            output_path = "dist/TelegramUserTracking"
            print(f"\n📦 Executable location: {output_path}")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def create_version_info():
    """Create version info file for Windows."""
    if platform.system() != 'Windows':
        return
    
    version_info = """
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'Telegram User Tracking Application'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'TelegramUserTracking'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
        StringStruct(u'OriginalFilename', u'TelegramUserTracking.exe'),
        StringStruct(u'ProductName', u'Telegram User Tracking'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    version_file = PROJECT_ROOT / 'version_info.txt'
    with open(version_file, 'w') as f:
        f.write(version_info)


if __name__ == '__main__':
    create_version_info()
    sys.exit(build_executable())
