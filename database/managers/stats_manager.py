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
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get statistics for dashboard."""
        with self.get_connection() as conn:
            stats = {}
            
            # Total messages
            cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = 0")
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Total users
            cursor = conn.execute("SELECT COUNT(*) FROM telegram_users WHERE is_deleted = 0")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Total groups
            cursor = conn.execute("SELECT COUNT(*) FROM telegram_groups")
            stats['total_groups'] = cursor.fetchone()[0]
            
            # Total media size
            cursor = conn.execute("SELECT SUM(file_size_bytes) FROM media_files")
            result = cursor.fetchone()[0]
            stats['total_media_size'] = result if result else 0
            
            # Messages today
            cursor = conn.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE date_sent >= date('now') AND is_deleted = 0
            """)
            stats['messages_today'] = cursor.fetchone()[0]
            
            # Messages this month
            cursor = conn.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE date_sent >= date('now', 'start of month') AND is_deleted = 0
            """)
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
        group_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top active users in a group sorted by message count."""
        encryption_service = self.get_encryption_service()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.full_name,
                    u.phone,
                    u.profile_photo_path,
                    COUNT(m.message_id) as message_count
                FROM telegram_users u
                INNER JOIN messages m ON u.user_id = m.user_id
                WHERE m.group_id = ? AND m.is_deleted = 0 AND u.is_deleted = 0
                GROUP BY u.user_id
                ORDER BY message_count DESC
                LIMIT ?
            """, (group_id, limit))
            
            results = []
            for row in cursor.fetchall():
                # Decrypt sensitive fields
                username = encryption_service.decrypt_field(row['username']) if encryption_service else row['username']
                first_name = encryption_service.decrypt_field(row['first_name']) if encryption_service else row['first_name']
                last_name = encryption_service.decrypt_field(row['last_name']) if encryption_service else row['last_name']
                full_name = encryption_service.decrypt_field(row['full_name']) if encryption_service else row['full_name']
                phone = encryption_service.decrypt_field(row['phone']) if encryption_service else row['phone']
                
                results.append({
                    'user_id': row['user_id'],
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'full_name': full_name,
                    'phone': phone,
                    'profile_photo_path': row['profile_photo_path'],
                    'message_count': row['message_count']
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

