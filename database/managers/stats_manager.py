"""
Statistics manager.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from database.managers.base import BaseDatabaseManager, _parse_datetime
import logging

logger = logging.getLogger(__name__)


class StatsManager(BaseDatabaseManager):
    """Manages statistics operations."""
    
    def get_dashboard_stats(
        self, 
        group_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics for dashboard.
        
        Args:
            group_ids: Optional list of group IDs to filter by. If None, includes all groups.
            start_date: Optional start date to filter by.
            end_date: Optional end date to filter by.
        """
        with self.get_connection() as conn:
            stats = {}
            
            # Build filter conditions
            conditions = ["is_deleted = 0"]
            params = []
            
            if group_ids and len(group_ids) > 0:
                placeholders = ",".join("?" * len(group_ids))
                conditions.append(f"group_id IN ({placeholders})")
                params.extend(group_ids)
            
            if start_date:
                conditions.append("date_sent >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("date_sent <= ?")
                params.append(end_date)
            
            where_clause = " AND ".join(conditions)
            
            # Total messages
            query = f"SELECT COUNT(*) FROM messages WHERE {where_clause}"
            cursor = conn.execute(query, params)
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Total users (distinct users from selected groups)
            if group_ids and len(group_ids) > 0:
                user_conditions = ["m.is_deleted = 0", "u.is_deleted = 0"]
                user_params = []
                
                placeholders = ",".join("?" * len(group_ids))
                user_conditions.append(f"m.group_id IN ({placeholders})")
                user_params.extend(group_ids)
                
                if start_date:
                    user_conditions.append("m.date_sent >= ?")
                    user_params.append(start_date)
                
                if end_date:
                    user_conditions.append("m.date_sent <= ?")
                    user_params.append(end_date)
                
                user_where = " AND ".join(user_conditions)
                query = f"""
                    SELECT COUNT(DISTINCT u.user_id) FROM telegram_users u
                    INNER JOIN messages m ON u.user_id = m.user_id
                    WHERE {user_where}
                """
                cursor = conn.execute(query, user_params)
                stats['total_users'] = cursor.fetchone()[0]
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM telegram_users WHERE is_deleted = 0")
                stats['total_users'] = cursor.fetchone()[0]
            
            # Total groups (count of selected groups or all groups)
            if group_ids and len(group_ids) > 0:
                placeholders = ",".join("?" * len(group_ids))
                query = f"SELECT COUNT(*) FROM telegram_groups WHERE group_id IN ({placeholders})"
                cursor = conn.execute(query, group_ids)
                stats['total_groups'] = cursor.fetchone()[0]
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM telegram_groups")
                stats['total_groups'] = cursor.fetchone()[0]
            
            # Total media size (from selected groups and date range)
            media_conditions = ["m.is_deleted = 0"]
            media_params = []
            
            if group_ids and len(group_ids) > 0:
                placeholders = ",".join("?" * len(group_ids))
                media_conditions.append(f"m.group_id IN ({placeholders})")
                media_params.extend(group_ids)
            
            if start_date:
                media_conditions.append("m.date_sent >= ?")
                media_params.append(start_date)
            
            if end_date:
                media_conditions.append("m.date_sent <= ?")
                media_params.append(end_date)
            
            media_where = " AND ".join(media_conditions)
            query = f"""
                SELECT SUM(mf.file_size_bytes) FROM media_files mf
                INNER JOIN messages m ON mf.message_id = m.message_id
                WHERE {media_where}
            """
            cursor = conn.execute(query, media_params)
            result = cursor.fetchone()[0]
            stats['total_media_size'] = result if result else 0
            
            # Messages today (within date range if specified)
            today_conditions = ["date_sent >= date('now')", "is_deleted = 0"]
            today_params = []
            
            if group_ids and len(group_ids) > 0:
                placeholders = ",".join("?" * len(group_ids))
                today_conditions.append(f"group_id IN ({placeholders})")
                today_params.extend(group_ids)
            
            today_where = " AND ".join(today_conditions)
            query = f"SELECT COUNT(*) FROM messages WHERE {today_where}"
            cursor = conn.execute(query, today_params)
            stats['messages_today'] = cursor.fetchone()[0]
            
            # Messages this month (within date range if specified)
            month_conditions = ["date_sent >= date('now', 'start of month')", "is_deleted = 0"]
            month_params = []
            
            if group_ids and len(group_ids) > 0:
                placeholders = ",".join("?" * len(group_ids))
                month_conditions.append(f"group_id IN ({placeholders})")
                month_params.extend(group_ids)
            
            month_where = " AND ".join(month_conditions)
            query = f"SELECT COUNT(*) FROM messages WHERE {month_where}"
            cursor = conn.execute(query, month_params)
            stats['messages_this_month'] = cursor.fetchone()[0]
            
            return stats
    
    def get_user_activity_stats(
        self,
        user_id: int,
        group_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive activity statistics for a user."""
        stats = {}
        
        with self.get_connection() as conn:
            # Build base query conditions
            msg_conditions = ["m.user_id = ?", "m.is_deleted = 0"]
            params = [user_id]
            
            if group_id:
                msg_conditions.append("m.group_id = ?")
                params.append(group_id)
            
            if start_date:
                msg_conditions.append("m.date_sent >= ?")
                params.append(start_date)
            
            if end_date:
                msg_conditions.append("m.date_sent <= ?")
                params.append(end_date)
            
            where_clause = " AND ".join(msg_conditions)
            
            # Total messages
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM messages m
                WHERE {where_clause}
            """, params)
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Total reactions given by user
            reaction_conditions = ["r.user_id = ?"]
            reaction_params = [user_id]
            
            if group_id:
                reaction_conditions.append("r.group_id = ?")
                reaction_params.append(group_id)
            
            reaction_where = " AND ".join(reaction_conditions)
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM reactions r
                WHERE {reaction_where}
            """, reaction_params)
            stats['total_reactions'] = cursor.fetchone()[0]
            
            # Message type breakdown
            cursor = conn.execute(f"""
                SELECT 
                    COUNT(CASE WHEN m.message_type = 'sticker' OR m.has_sticker = 1 THEN 1 END) as stickers,
                    COUNT(CASE WHEN m.message_type = 'video' OR m.media_type = 'video' THEN 1 END) as videos,
                    COUNT(CASE WHEN m.message_type = 'photo' OR m.media_type = 'photo' THEN 1 END) as photos,
                    COUNT(CASE WHEN m.has_link = 1 THEN 1 END) as links,
                    COUNT(CASE WHEN m.message_type = 'document' OR m.media_type = 'document' THEN 1 END) as documents,
                    COUNT(CASE WHEN m.message_type IN ('audio', 'voice') OR m.media_type = 'audio' THEN 1 END) as audio,
                    COUNT(CASE WHEN m.message_type = 'text' OR (m.content IS NOT NULL AND m.content != '') THEN 1 END) as text_messages
                FROM messages m
                WHERE {where_clause}
            """, params)
            row = cursor.fetchone()
            stats['total_stickers'] = row[0] or 0
            stats['total_videos'] = row[1] or 0
            stats['total_photos'] = row[2] or 0
            stats['total_links'] = row[3] or 0
            stats['total_documents'] = row[4] or 0
            stats['total_audio'] = row[5] or 0
            stats['total_text_messages'] = row[6] or 0
            
            # First and last activity dates
            cursor = conn.execute(f"""
                SELECT MIN(m.date_sent), MAX(m.date_sent)
                FROM messages m
                WHERE {where_clause}
            """, params)
            row = cursor.fetchone()
            stats['first_activity_date'] = _parse_datetime(row[0]) if row[0] else None
            stats['last_activity_date'] = _parse_datetime(row[1]) if row[1] else None
            
            # Messages by group (if group_id not specified)
            if not group_id:
                cursor = conn.execute(f"""
                    SELECT m.group_id, COUNT(*) as count
                    FROM messages m
                    WHERE {where_clause}
                    GROUP BY m.group_id
                """, params)
                stats['messages_by_group'] = {row[0]: row[1] for row in cursor.fetchall()}
            else:
                stats['messages_by_group'] = {}
        
        return stats
    
    def get_message_type_breakdown(
        self,
        user_id: int,
        group_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get detailed message type breakdown for a user."""
        conditions = ["user_id = ?", "is_deleted = 0"]
        params = [user_id]
        
        if group_id:
            conditions.append("group_id = ?")
            params.append(group_id)
        
        where_clause = " AND ".join(conditions)
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT 
                    COALESCE(message_type, 'unknown') as msg_type,
                    COUNT(*) as count
                FROM messages
                WHERE {where_clause}
                GROUP BY msg_type
            """, params)
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_top_active_users_by_group(
        self,
        group_id: Optional[int] = None,
        group_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top active users in group(s) sorted by message count.
        
        Args:
            group_id: Single group ID (for backward compatibility)
            group_ids: List of group IDs to filter by (takes precedence over group_id)
            limit: Maximum number of users to return
        """
        encryption_service = self.get_encryption_service()
        
        # Use group_ids if provided, otherwise use group_id
        if group_ids and len(group_ids) > 0:
            target_group_ids = group_ids
        elif group_id:
            target_group_ids = [group_id]
        else:
            return []
        
        with self.get_connection() as conn:
            placeholders = ",".join("?" * len(target_group_ids))
            conditions = [
                f"m.group_id IN ({placeholders})",
                "m.is_deleted = 0",
                "u.is_deleted = 0"
            ]
            params = list(target_group_ids)
            
            if start_date:
                conditions.append("m.date_sent >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("m.date_sent <= ?")
                params.append(end_date)
            
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.full_name,
                    u.phone,
                    u.profile_photo_path,
                    COUNT(m.message_id) as message_count,
                    MAX(m.date_sent) as last_activity_date
                FROM telegram_users u
                INNER JOIN messages m ON u.user_id = m.user_id
                WHERE {where_clause}
                GROUP BY u.user_id
                ORDER BY message_count DESC
                LIMIT ?
            """
            params.append(limit)
            cursor = conn.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                # Decrypt sensitive fields
                username = encryption_service.decrypt_field(row['username']) if encryption_service else row['username']
                first_name = encryption_service.decrypt_field(row['first_name']) if encryption_service else row['first_name']
                last_name = encryption_service.decrypt_field(row['last_name']) if encryption_service else row['last_name']
                full_name = encryption_service.decrypt_field(row['full_name']) if encryption_service else row['full_name']
                phone = encryption_service.decrypt_field(row['phone']) if encryption_service else row['phone']
                
                last_activity = _parse_datetime(row['last_activity_date']) if row['last_activity_date'] else None
                
                results.append({
                    'user_id': row['user_id'],
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'full_name': full_name,
                    'phone': phone,
                    'profile_photo_path': row['profile_photo_path'],
                    'message_count': row['message_count'],
                    'last_activity_date': last_activity
                })
            
            return results
    
    def get_group_summaries(self) -> List[Dict[str, Any]]:
        """Get summary statistics for all groups."""
        with self.get_connection() as conn:
            # Get all groups with their statistics
            cursor = conn.execute("""
                SELECT 
                    g.group_id,
                    g.group_name,
                    g.group_photo_path,
                    g.last_fetch_date,
                    COUNT(DISTINCT m.message_id) as total_messages,
                    COUNT(DISTINCT m.user_id) as active_members,
                    COUNT(DISTINCT u.user_id) as total_members,
                    COUNT(DISTINCT fh.id) as export_history_count,
                    MAX(fh.end_date) as last_export_date
                FROM telegram_groups g
                LEFT JOIN messages m ON g.group_id = m.group_id AND m.is_deleted = 0
                LEFT JOIN telegram_users u ON u.user_id = m.user_id AND u.is_deleted = 0
                LEFT JOIN group_fetch_history fh ON g.group_id = fh.group_id
                GROUP BY g.group_id, g.group_name, g.group_photo_path, g.last_fetch_date
                ORDER BY g.group_name
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'group_id': row['group_id'],
                    'group_name': row['group_name'],
                    'group_photo_path': row['group_photo_path'],
                    'last_fetch_date': _parse_datetime(row['last_fetch_date']),
                    'total_messages': row['total_messages'] or 0,
                    'active_members': row['active_members'] or 0,
                    'total_members': row['total_members'] or 0,
                    'export_history_count': row['export_history_count'] or 0,
                    'last_export_date': _parse_datetime(row['last_export_date'])
                })
            
            return results

