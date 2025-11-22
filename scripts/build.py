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

# Get project root (parent of scripts/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Code protection settings
USE_PYARMOR = True  # Set to False to disable PyArmor obfuscation
USE_BYTECODE_ENCRYPTION = False  # DISABLED: PyInstaller removed --key option in v6.0+
REMOVE_SOURCE_FILES = True  # Remove .py files after build

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
        'tests', 'z_sanbox', 'unused', 'scripts',
        'pytest', 'pytest_', 'test_single_instance_manual',
        'decrypt_pin', 'icon_maker',
    ]
    
    print("\nExcluding from build:")
    for module in exclude_modules:
        print(f"  - {module}")
        cmd.extend(['--exclude-module', module])
    
    # Hidden imports
    hidden_imports = [
        'flet', 'telethon', 'firebase_admin', 'pandas',
        'xlsxwriter', 'reportlab', 'PIL', 'dotenv', 'cryptography',
        'qrcode',  # QR code generation
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
        if system == 'Darwin':
            resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking.app' / 'Contents' / 'Resources'
        elif system == 'Windows':
            if build_mode == '--onedir':
                resources_dir = PROJECT_ROOT / 'dist' / 'TelegramUserTracking'
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
        elif system == 'Darwin':
            output_path = "dist/TelegramUserTracking.app"
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
