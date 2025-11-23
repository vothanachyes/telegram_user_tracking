"""
Skeleton loader components for page loading states.
"""

from ui.components.skeleton_loaders.base import (
    SkeletonCard,
    SkeletonRow,
    SkeletonCircle,
    SkeletonText,
    SkeletonTable,
    SkeletonButton,
    create_shimmer_animation
)
from ui.components.skeleton_loaders.dashboard_skeleton import DashboardSkeleton
from ui.components.skeleton_loaders.groups_skeleton import GroupsSkeleton
from ui.components.skeleton_loaders.user_dashboard_skeleton import UserDashboardSkeleton
from ui.components.skeleton_loaders.telegram_skeleton import TelegramSkeleton
from ui.components.skeleton_loaders.reports_skeleton import ReportsSkeleton
from ui.components.skeleton_loaders.notifications_skeleton import NotificationsSkeleton
from ui.components.skeleton_loaders.about_skeleton import AboutSkeleton
from ui.components.skeleton_loaders.settings_skeleton import SettingsSkeleton
from ui.components.skeleton_loaders.general_skeleton import GeneralSkeleton

__all__ = [
    'SkeletonCard',
    'SkeletonRow',
    'SkeletonCircle',
    'SkeletonText',
    'SkeletonTable',
    'SkeletonButton',
    'create_shimmer_animation',
    'DashboardSkeleton',
    'GroupsSkeleton',
    'UserDashboardSkeleton',
    'TelegramSkeleton',
    'ReportsSkeleton',
    'NotificationsSkeleton',
    'AboutSkeleton',
    'SettingsSkeleton',
    'GeneralSkeleton',
]

