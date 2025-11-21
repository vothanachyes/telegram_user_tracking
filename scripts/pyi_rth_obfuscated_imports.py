"""
PyInstaller runtime hook to fix imports for PyArmor obfuscated modules.

This hook adds the Resources directory to sys.path so that obfuscated
modules in nested directories (e.g., utils/utils/) can be imported correctly.
"""
import sys
import os
from pathlib import Path

# Get the Resources directory (where PyInstaller puts data files)
if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    if sys.platform == 'darwin':
        # macOS: Resources is in Contents/Resources
        bundle_dir = Path(sys.executable).parent.parent.parent
        resources_dir = bundle_dir / 'Contents' / 'Resources'
    elif sys.platform == 'win32':
        # Windows: Resources is in the same directory as the exe
        resources_dir = Path(sys.executable).parent
    else:
        # Linux: Resources is in the same directory as the executable
        resources_dir = Path(sys.executable).parent
    
    if resources_dir.exists():
        # Add Resources to sys.path so modules can be imported
        resources_str = str(resources_dir)
        if resources_str not in sys.path:
            sys.path.insert(0, resources_str)
        
        # Also handle nested structure: if utils/utils/ exists, add utils/ to path
        # This allows imports like "from utils.logging_config import ..." to work
        utils_nested = resources_dir / 'utils' / 'utils'
        if utils_nested.exists():
            utils_dir = resources_dir / 'utils'
            utils_str = str(utils_dir)
            if utils_str not in sys.path:
                sys.path.insert(0, utils_str)

