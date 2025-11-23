"""
Build script for creating executable with PyInstaller.
Includes code protection: PyArmor obfuscation and source file removal.
Note: Bytecode encryption (--key) was removed in PyInstaller v6.0+
"""
import os
import sys
import platform
from pathlib import Path

# Import from modular build system
from scripts.build.config import (
    PROJECT_ROOT, USE_PYARMOR, USE_INSTALLER, REMOVE_SOURCE_FILES,
    USE_BYTECODE_ENCRYPTION, OBFUSCATED_DIR, APP_NAME, APP_VERSION, DEVELOPER_NAME
)
from scripts.build.obfuscation import obfuscate_code
from scripts.build.installer import build_installer
from scripts.build.pyinstaller_config import build_executable
from scripts.build.cleanup import (
    cleanup_before_build, cleanup_after_build, update_macos_info_plist
)


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


def main():
    """Main build orchestration."""
    system = platform.system()
    build_mode = '--onedir' if system == 'Darwin' else '--onefile'
    
    # Clean up before build
    cleanup_before_build()
    
    # Step 1: Obfuscate code (if enabled)
    obfuscation_success = obfuscate_code()
    
    # Step 2: Build executable
    result = build_executable(obfuscation_success)
    if result != 0:
        return result
    
    # Step 3: Cleanup after build
    cleanup_after_build(system, build_mode, obfuscation_success)
    
    # Step 4: Update macOS Info.plist
    update_macos_info_plist()
    
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
    
    # Print summary
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


if __name__ == '__main__':
    create_version_info()
    sys.exit(main())
