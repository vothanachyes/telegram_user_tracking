"""
Build script for creating executable with PyInstaller.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def build_executable():
    """Build executable for current platform."""
    
    print("=" * 60)
    print("Telegram User Tracking - Build Script")
    print("=" * 60)
    
    # Get platform info
    system = platform.system()
    print(f"\nBuilding for: {system}")
    
    # Base PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=TelegramUserTracking',
        '--onefile',
        '--windowed',
        '--clean',
        'main.py',
    ]
    
    # Add icon if available
    icon_path = Path('assets/icon.png')
    if icon_path.exists():
        if system == 'Windows':
            # Convert PNG to ICO if needed
            cmd.extend(['--icon=assets/icon.ico'])
        elif system == 'Darwin':  # macOS
            cmd.extend(['--icon=assets/icon.icns'])
    
    # Add data files
    cmd.extend([
        '--add-data=config:config',
        '--add-data=database:database',
        '--add-data=services:services',
        '--add-data=ui:ui',
        '--add-data=utils:utils',
    ])
    
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
    
    with open('version_info.txt', 'w') as f:
        f.write(version_info)


if __name__ == '__main__':
    create_version_info()
    sys.exit(build_executable())

