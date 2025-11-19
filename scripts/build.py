"""
Build script for creating executable with PyInstaller.
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

# Get project root (parent of scripts/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_executable():
    """Build executable for current platform."""
    
    print("=" * 60)
    print("Telegram User Tracking - Build Script")
    print("=" * 60)
    
    # Get platform info
    system = platform.system()
    print(f"\nBuilding for: {system}")
    
    # Change to project root directory for build
    os.chdir(PROJECT_ROOT)
    
    # Base PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=TelegramUserTracking',
        '--onefile',
        '--windowed',
        '--clean',
        'main.py',
    ]
    
    # Add icon if available (from assets/icons directory)
    icon_added = False
    if system == 'Windows':
        # Check for Windows icon from assets/icons/win
        win_icon = PROJECT_ROOT / 'assets' / 'icons' / 'win' / 'icon.ico'
        if win_icon.exists():
            cmd.extend(['--icon=assets/icons/win/icon.ico'])
            icon_added = True
            print(f"Using icon: {win_icon}")
        else:
            # Fallback to assets root if icon_maker output doesn't exist
            fallback_icon = PROJECT_ROOT / 'assets' / 'icon.ico'
            if fallback_icon.exists():
                cmd.extend(['--icon=assets/icon.ico'])
                icon_added = True
                print(f"Using fallback icon: {fallback_icon}")
    elif system == 'Darwin':  # macOS
        # Check for macOS icon from assets/icons/mac
        mac_icon = PROJECT_ROOT / 'assets' / 'icons' / 'mac' / 'icon.icns'
        if mac_icon.exists():
            cmd.extend(['--icon=assets/icons/mac/icon.icns'])
            icon_added = True
            print(f"Using icon: {mac_icon}")
        else:
            # Fallback to assets root if icon_maker output doesn't exist
            fallback_icon = PROJECT_ROOT / 'assets' / 'icon.icns'
            if fallback_icon.exists():
                cmd.extend(['--icon=assets/icon.icns'])
                icon_added = True
                print(f"Using fallback icon: {fallback_icon}")
    
    if not icon_added:
        print("⚠️  No icon found - building without icon")
    
    # Add data files (only production code)
    data_files = [
        '--add-data=config:config',
        '--add-data=database:database',
        '--add-data=services:services',
        '--add-data=ui:ui',
        '--add-data=utils:utils',
    ]
    
    # Add locales if they exist
    if (PROJECT_ROOT / 'locales').exists():
        data_files.append('--add-data=locales:locales')
    
    # Add assets if they exist
    if (PROJECT_ROOT / 'assets').exists():
        data_files.append('--add-data=assets:assets')
    
    cmd.extend(data_files)
    
    # Exclude unrelated code from build
    exclude_modules = [
        'data_ran',           # Test data generator
        'tests',              # Test files
        'z_sanbox',           # Sandbox/development files
        'unused',             # Unused files
        'scripts',            # Build/utility scripts
        'pytest',             # Testing framework
        'pytest_',            # Any pytest plugins
        'dataRan',            # Test data generator entry point
        'test_single_instance_manual',  # Test script
        'decrypt_pin',        # Utility script
        'icon_maker',         # Icon generation script
    ]
    
    print("\nExcluding from build:")
    for module in exclude_modules:
        print(f"  - {module}")
        cmd.extend(['--exclude-module', module])
    
    # Hidden imports
    hidden_imports = [
        'flet',
        'telethon',
        'firebase_admin',
        'pandas',
        'xlsxwriter',
        'reportlab',
        'PIL',
        'dotenv',
        'cryptography',
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Build info
    cmd.extend([
        '--version-file=version_info.txt' if system == 'Windows' else '',
    ])
    
    # Remove empty strings
    cmd = [c for c in cmd if c]
    
    print("\nRunning PyInstaller...")
    print(" ".join(cmd))
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        print(f"\nExecutable location: dist/TelegramUserTracking{'.exe' if system == 'Windows' else ''}")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
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

