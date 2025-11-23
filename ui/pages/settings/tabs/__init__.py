"""
Settings page tabs package.
"""

from ui.pages.settings.tabs.general_tab import GeneralTab
from ui.pages.settings.tabs.authenticate_tab import AuthenticateTab
from ui.pages.settings.tabs.configure_tab import ConfigureTab
from ui.pages.settings.tabs.security_tab import SecurityTab
from ui.pages.settings.tabs.data_tab import DataTab
from ui.pages.settings.tabs.devices_tab.page import DevicesTab

__all__ = ['GeneralTab', 'AuthenticateTab', 'ConfigureTab', 'SecurityTab', 'DataTab', 'DevicesTab']

