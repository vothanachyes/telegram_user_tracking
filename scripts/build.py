"""
Build script for creating executable with PyInstaller.
Includes code protection: PyArmor obfuscation, bytecode encryption, and source file removal.
"""
import os
import sys
import platform
import subprocess
import shutil
import secrets
from pathlib import Path

# Get project root (parent of scripts/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Code protection settings
USE_PYARMOR = True  # Set to False to disable PyArmor obfuscation
USE_BYTECODE_ENCRYPTION = True  # PyInstaller --key option (works with or without PyArmor)
REMOVE_SOURCE_FILES = True  # Remove .py files after build

# Generate or load encryption key for PyInstaller
ENCRYPTION_KEY_FILE = PROJECT_ROOT / '.build_key'
OBFUSCATED_DIR = PROJECT_ROOT / 'obfuscated_temp'


def get_or_create_encryption_key() -> str:
    """Get existing encryption key or create a new one."""
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, 'r') as f:
            return f.read().strip()
    else:
        # Generate a 16-byte hex key
        key = secrets.token_hex(16)
        with open(ENCRYPTION_KEY_FILE, 'w') as f:
            f.write(key)
        print(f"Generated new encryption key: {ENCRYPTION_KEY_FILE}")
        return key


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
    
    # Add bytecode encryption (Option 2)
    if USE_BYTECODE_ENCRYPTION:
        encryption_key = get_or_create_encryption_key()
        cmd.extend(['--key', encryption_key])
        print(f"  Using bytecode encryption (key from: {ENCRYPTION_KEY_FILE.name})")
    
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
    
    # If using obfuscated code, we need to adjust paths
    if USE_PYARMOR and obfuscation_success and OBFUSCATED_DIR.exists():
        # For obfuscated builds, use obfuscated code directories
        # But keep data files (JSON, etc.) from original
        data_files = [
            f'--add-data={OBFUSCATED_DIR}/config:config',
            f'--add-data={OBFUSCATED_DIR}/database:database',
            f'--add-data={OBFUSCATED_DIR}/services:services',
            f'--add-data={OBFUSCATED_DIR}/ui:ui',
            f'--add-data={OBFUSCATED_DIR}/utils:utils',
        ]
    
    # Add locales if they exist
    if (PROJECT_ROOT / 'locales').exists():
        data_files.append('--add-data=locales:locales')
    
    # Add assets if they exist
    if (PROJECT_ROOT / 'assets').exists():
        data_files.append('--add-data=assets:assets')
    
    # Check for Firebase credentials JSON files in config/
    config_dir = PROJECT_ROOT / 'config'
    firebase_creds = list(config_dir.glob('*.json'))
    if firebase_creds:
        print(f"\nFound Firebase credentials file(s):")
        for cred_file in firebase_creds:
            print(f"  - {cred_file.name}")
    else:
        print("\n⚠️  No Firebase credentials JSON file found in config/")
        print("   Firebase features may not work in production")
    
    cmd.extend(data_files)
    
    # Exclude unrelated code from build
    exclude_modules = [
        'data_ran', 'tests', 'z_sanbox', 'unused', 'scripts',
        'pytest', 'pytest_', 'dataRan', 'test_single_instance_manual',
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
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
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
        if REMOVE_SOURCE_FILES:
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
            else:
                print(f"  ⚠️  Resources directory not found: {resources_dir}")
        
        # Clean up obfuscated temp directory
        if OBFUSCATED_DIR.exists():
            print(f"\nCleaning up obfuscation temp directory...")
            shutil.rmtree(OBFUSCATED_DIR)
        
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
            print("  ✅ Bytecode encryption: ENABLED")
        else:
            print("  ⚠️  Bytecode encryption: DISABLED")
        
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
