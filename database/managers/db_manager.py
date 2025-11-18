"""
Main database manager that composes all domain managers.
"""

from database.managers.base import BaseDatabaseManager
from database.managers.settings_manager import SettingsManager
from database.managers.telegram_credential_manager import TelegramCredentialManager
from database.managers.group_manager import GroupManager
from database.managers.fetch_history_manager import FetchHistoryManager
from database.managers.user_manager import UserManager
from database.managers.message_manager import MessageManager
from database.managers.media_manager import MediaManager
from database.managers.reaction_manager import ReactionManager
from database.managers.stats_manager import StatsManager
from database.managers.auth_manager import AuthManager
from database.managers.license_manager import LicenseManager
from database.managers.account_activity_manager import AccountActivityManager
from database.managers.update_manager import UpdateManager
from database.managers.tag_manager import TagManager


class DatabaseManager(BaseDatabaseManager):
    """
    Main database manager that composes all domain managers.
    Maintains the same public API as the original DatabaseManager.
    """
    
    def __init__(self, db_path: str = "./data/app.db"):
        """Initialize database manager with all composed managers."""
        # Initialize base class which sets up the database
        super().__init__(db_path)
        
        # Compose all domain managers
        self._settings = SettingsManager(db_path)
        self._telegram_credential = TelegramCredentialManager(db_path)
        self._group = GroupManager(db_path)
        self._fetch_history = FetchHistoryManager(db_path)
        self._user = UserManager(db_path)
        self._message = MessageManager(db_path)
        self._media = MediaManager(db_path)
        self._reaction = ReactionManager(db_path)
        self._stats = StatsManager(db_path)
        self._auth = AuthManager(db_path)
        self._license = LicenseManager(db_path)
        self._account_activity = AccountActivityManager(db_path)
        self._update = UpdateManager(db_path)
        self._tag = TagManager(db_path)
    
    # Delegate all methods to composed managers
    # App Settings
    def get_settings(self):
        return self._settings.get_settings()
    
    def update_settings(self, settings):
        return self._settings.update_settings(settings)
    
    # Telegram Credentials
    def save_telegram_credential(self, credential):
        return self._telegram_credential.save_telegram_credential(credential)
    
    def get_telegram_credentials(self):
        return self._telegram_credential.get_telegram_credentials()
    
    def get_default_credential(self):
        return self._telegram_credential.get_default_credential()
    
    def get_credential_by_id(self, credential_id):
        return self._telegram_credential.get_credential_by_id(credential_id)
    
    def delete_telegram_credential(self, credential_id):
        return self._telegram_credential.delete_telegram_credential(credential_id)
    
    def get_credential_with_status(self, credential_id):
        return self._telegram_credential.get_credential_with_status(credential_id)
    
    def get_all_credentials_with_status(self):
        return self._telegram_credential.get_all_credentials_with_status()
    
    def account_exists(self, phone_number):
        return self._telegram_credential.account_exists(phone_number)
    
    def get_account_count(self):
        return self._telegram_credential.get_account_count()
    
    # Groups
    def save_group(self, group):
        return self._group.save_group(group)
    
    def get_all_groups(self):
        return self._group.get_all_groups()
    
    def get_group_by_id(self, group_id):
        return self._group.get_group_by_id(group_id)
    
    # Fetch History
    def save_fetch_history(self, history):
        return self._fetch_history.save_fetch_history(history)
    
    def get_fetch_history_by_group(self, group_id):
        return self._fetch_history.get_fetch_history_by_group(group_id)
    
    def get_all_fetch_history(self):
        return self._fetch_history.get_all_fetch_history()
    
    # Users
    def save_user(self, user):
        return self._user.save_user(user)
    
    def get_all_users(self, include_deleted=False):
        return self._user.get_all_users(include_deleted)
    
    def get_user_by_id(self, user_id):
        return self._user.get_user_by_id(user_id)
    
    def get_users_by_group(self, group_id, include_deleted=False):
        return self._user.get_users_by_group(group_id, include_deleted)
    
    def search_users(self, query, limit=10, include_deleted=False):
        return self._user.search_users(query, limit, include_deleted)
    
    def soft_delete_user(self, user_id):
        return self._user.soft_delete_user(user_id)
    
    # Messages
    def save_message(self, message):
        return self._message.save_message(message)
    
    def get_messages(self, group_id=None, user_id=None, start_date=None, end_date=None,
                     include_deleted=False, limit=None, offset=0, tags=None):
        return self._message.get_messages(group_id, user_id, start_date, end_date,
                                         include_deleted, limit, offset, tags)
    
    def get_message_count(self, group_id=None, user_id=None, include_deleted=False):
        return self._message.get_message_count(group_id, user_id, include_deleted)
    
    def soft_delete_message(self, message_id, group_id):
        return self._message.soft_delete_message(message_id, group_id)
    
    def is_message_deleted(self, message_id, group_id):
        return self._message.is_message_deleted(message_id, group_id)
    
    def message_exists(self, message_id, group_id):
        return self._message.message_exists(message_id, group_id)
    
    def undelete_message(self, message_id, group_id):
        return self._message.undelete_message(message_id, group_id)
    
    # Media
    def save_media_file(self, media):
        return self._media.save_media_file(media)
    
    def get_media_for_message(self, message_id):
        return self._media.get_media_for_message(message_id)
    
    def get_total_media_size(self):
        return self._media.get_total_media_size()
    
    # Reactions
    def save_reaction(self, reaction):
        return self._reaction.save_reaction(reaction)
    
    def get_reactions_by_message(self, message_id, group_id):
        return self._reaction.get_reactions_by_message(message_id, group_id)
    
    def get_reactions_by_user(self, user_id, group_id=None):
        return self._reaction.get_reactions_by_user(user_id, group_id)
    
    def delete_reaction(self, reaction_id):
        return self._reaction.delete_reaction(reaction_id)
    
    # Statistics
    def get_top_active_users_by_group(self, group_id, limit=10):
        return self._stats.get_top_active_users_by_group(group_id, limit)
    
    def get_group_summaries(self):
        return self._stats.get_group_summaries()
    def get_dashboard_stats(self):
        return self._stats.get_dashboard_stats()
    
    def get_user_activity_stats(self, user_id, group_id=None, start_date=None, end_date=None):
        return self._stats.get_user_activity_stats(user_id, group_id, start_date, end_date)
    
    def get_message_type_breakdown(self, user_id, group_id=None):
        return self._stats.get_message_type_breakdown(user_id, group_id)
    
    # Auth
    def save_login_credential(self, email, encrypted_password):
        return self._auth.save_login_credential(email, encrypted_password)
    
    def get_login_credential(self):
        return self._auth.get_login_credential()
    
    def delete_login_credential(self, email=None):
        return self._auth.delete_login_credential(email)
    
    # License
    def save_license_cache(self, license_cache):
        return self._license.save_license_cache(license_cache)
    
    def get_license_cache(self, user_email):
        return self._license.get_license_cache(user_email)
    
    def delete_license_cache(self, user_email):
        return self._license.delete_license_cache(user_email)
    
    # Account Activity
    def log_account_action(self, user_email, action, phone_number=None):
        return self._account_activity.log_account_action(user_email, action, phone_number)
    
    def get_recent_activity_count(self, user_email, hours=48):
        return self._account_activity.get_recent_activity_count(user_email, hours)
    
    def can_perform_account_action(self, user_email, max_actions=2):
        return self._account_activity.can_perform_account_action(user_email, max_actions=max_actions)
    
    def get_waiting_time_hours(self, user_email, max_actions=2, hours=48):
        return self._account_activity.get_waiting_time_hours(user_email, max_actions=max_actions, hours=hours)
    
    def get_activity_log(self, user_email, limit=10):
        return self._account_activity.get_activity_log(user_email, limit)
    
    # Update History
    def record_update_installation(self, user_email, version, download_path=None):
        return self._update.record_update_installation(user_email, version, download_path)
    
    def get_user_installed_versions(self, user_email):
        return self._update.get_user_installed_versions(user_email)
    
    def has_user_installed_version(self, user_email, version):
        return self._update.has_user_installed_version(user_email, version)
    
    # Tags
    def get_tag_suggestions(self, prefix, group_id=None, limit=10):
        return self._tag.get_tag_suggestions(prefix, group_id, limit)
    
    def get_all_tags_for_group(self, group_id):
        return self._tag.get_all_tags_for_group(group_id)
    
    def get_tag_counts_by_group(self, group_id):
        return self._tag.get_tag_counts_by_group(group_id)

