"""
UI Pages package.
"""

from ui.pages.login_page import LoginPage
from ui.pages.dashboard.page import DashboardPage
from ui.pages.settings.page import SettingsPage
from ui.pages.telegram.page import TelegramPage
from ui.pages.profile_page import ProfilePage
from ui.pages.user_dashboard.page import UserDashboardPage
from ui.pages.about.page import AboutPage
from ui.pages.fetch_data.page import FetchDataPage
from ui.pages.groups.page import GroupsPage

__all__ = ['LoginPage', 'DashboardPage', 'SettingsPage', 'TelegramPage', 'ProfilePage', 'UserDashboardPage', 'AboutPage', 'FetchDataPage', 'GroupsPage']

