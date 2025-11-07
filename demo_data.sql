-- =====================================================
-- Telegram User Tracking - Demo Data SQL Dump
-- =====================================================
-- This file contains example data for QA testing
-- Demonstrates all features: messages, reactions, media, 
-- deleted items, licenses, and various message types
-- =====================================================

-- Disable foreign key checks temporarily
PRAGMA foreign_keys = OFF;

-- =====================================================
-- 1. APP SETTINGS (1 record)
-- =====================================================
INSERT OR REPLACE INTO app_settings (
    id, theme, language, corner_radius, 
    telegram_api_id, telegram_api_hash,
    download_root_dir, download_media, max_file_size_mb,
    fetch_delay_seconds, download_photos, download_videos,
    download_documents, download_audio, track_reactions,
    reaction_fetch_delay, created_at, updated_at
) VALUES (
    1, 'dark', 'en', 10,
    '12345678', 'abcdef1234567890abcdef1234567890',
    './downloads', 1, 50,
    1.0, 1, 1,
    1, 1, 1,
    0.5, '2024-01-15 10:00:00', '2024-01-20 14:30:00'
);

-- =====================================================
-- 2. TELEGRAM CREDENTIALS (2 records)
-- =====================================================
INSERT OR REPLACE INTO telegram_credentials (
    id, phone_number, session_string, is_default, 
    last_used, created_at
) VALUES 
(1, '+1234567890', 'encrypted_session_string_1', 1, '2024-01-20 12:00:00', '2024-01-15 10:00:00'),
(2, '+9876543210', 'encrypted_session_string_2', 0, '2024-01-19 15:30:00', '2024-01-16 11:00:00');

-- =====================================================
-- 3. TELEGRAM GROUPS (3 groups)
-- =====================================================
INSERT OR REPLACE INTO telegram_groups (
    id, group_id, group_name, group_username,
    last_fetch_date, total_messages, created_at, updated_at
) VALUES 
(1, -1001234567890, 'Tech Developers Community', 'techdevs', '2024-01-20 14:00:00', 8, '2024-01-15 10:00:00', '2024-01-20 14:00:00'),
(2, -1001234567891, 'Marketing Team', 'marketing_team', '2024-01-19 16:00:00', 5, '2024-01-16 11:00:00', '2024-01-19 16:00:00'),
(3, -1001234567892, 'Project Management', NULL, '2024-01-18 10:00:00', 2, '2024-01-17 09:00:00', '2024-01-18 10:00:00');

-- =====================================================
-- 4. TELEGRAM USERS (5 users - 1 deleted)
-- =====================================================
INSERT OR REPLACE INTO telegram_users (
    id, user_id, username, first_name, last_name, full_name,
    phone, bio, profile_photo_path, is_deleted, created_at, updated_at
) VALUES 
(1, 123456789, 'john_doe', 'John', 'Doe', 'John Doe', '+1234567890', 'Software Engineer | Python Enthusiast', './downloads/profiles/user_123456789.jpg', 0, '2024-01-15 10:00:00', '2024-01-20 12:00:00'),
(2, 234567890, 'jane_smith', 'Jane', 'Smith', 'Jane Smith', '+2345678901', 'Product Manager | UX Designer', './downloads/profiles/user_234567890.jpg', 0, '2024-01-15 10:05:00', '2024-01-19 15:00:00'),
(3, 345678901, 'alex_wilson', 'Alex', 'Wilson', 'Alex Wilson', '+3456789012', 'Full Stack Developer', './downloads/profiles/user_345678901.jpg', 0, '2024-01-15 10:10:00', '2024-01-18 14:00:00'),
(4, 456789012, 'sarah_jones', 'Sarah', 'Jones', 'Sarah Jones', '+4567890123', 'Marketing Specialist', './downloads/profiles/user_456789012.jpg', 0, '2024-01-16 11:00:00', '2024-01-19 16:00:00'),
(5, 567890123, 'deleted_user', 'Deleted', 'User', 'Deleted User', '+5678901234', NULL, NULL, 1, '2024-01-15 10:15:00', '2024-01-17 10:00:00');

-- =====================================================
-- 5. MESSAGES (15 messages - various types)
-- =====================================================
INSERT OR REPLACE INTO messages (
    id, message_id, group_id, user_id, content, caption,
    date_sent, has_media, media_type, media_count,
    message_link, message_type, has_sticker, has_link,
    sticker_emoji, is_deleted, created_at, updated_at
) VALUES 
-- Group 1: Tech Developers Community (8 messages)
(1, 1001, -1001234567890, 123456789, 'Hey everyone! Check out this new Python library: https://github.com/example/awesome-lib', NULL, '2024-01-15 10:30:00', 0, NULL, 0, 'https://t.me/techdevs/1001', 'text', 0, 1, NULL, 0, '2024-01-15 10:30:00', '2024-01-15 10:30:00'),
(2, 1002, -1001234567890, 234567890, NULL, 'Screenshot of the new UI design', '2024-01-15 11:00:00', 1, 'photo', 1, 'https://t.me/techdevs/1002', 'photo', 0, 0, NULL, 0, '2024-01-15 11:00:00', '2024-01-15 11:00:00'),
(3, 1003, -1001234567890, 345678901, NULL, NULL, '2024-01-15 11:30:00', 1, 'video', 1, 'https://t.me/techdevs/1003', 'video', 0, 0, NULL, 0, '2024-01-15 11:30:00', '2024-01-15 11:30:00'),
(4, 1004, -1001234567890, 123456789, NULL, NULL, '2024-01-15 12:00:00', 0, NULL, 0, 'https://t.me/techdevs/1004', 'sticker', 1, 0, '👍', 0, '2024-01-15 12:00:00', '2024-01-15 12:00:00'),
(5, 1005, -1001234567890, 234567890, 'Here is the project documentation PDF', NULL, '2024-01-15 13:00:00', 1, 'document', 1, 'https://t.me/techdevs/1005', 'document', 0, 0, NULL, 0, '2024-01-15 13:00:00', '2024-01-15 13:00:00'),
(6, 1006, -1001234567890, 345678901, NULL, NULL, '2024-01-15 14:00:00', 1, 'audio', 1, 'https://t.me/techdevs/1006', 'audio', 0, 0, NULL, 0, '2024-01-15 14:00:00', '2024-01-15 14:00:00'),
(7, 1007, -1001234567890, 123456789, 'Great work team! 🎉 Visit our website: https://example.com for more info', NULL, '2024-01-15 15:00:00', 0, NULL, 0, 'https://t.me/techdevs/1007', 'text', 0, 1, NULL, 0, '2024-01-15 15:00:00', '2024-01-15 15:00:00'),
(8, 1008, -1001234567890, 234567890, NULL, NULL, '2024-01-15 16:00:00', 0, NULL, 0, 'https://t.me/techdevs/1008', 'sticker', 1, 0, '🔥', 0, '2024-01-15 16:00:00', '2024-01-15 16:00:00'),

-- Group 2: Marketing Team (5 messages)
(9, 2001, -1001234567891, 456789012, 'New campaign launch next week! Check the details: https://campaign.example.com', NULL, '2024-01-16 09:00:00', 0, NULL, 0, 'https://t.me/marketing_team/2001', 'text', 0, 1, NULL, 0, '2024-01-16 09:00:00', '2024-01-16 09:00:00'),
(10, 2002, -1001234567891, 234567890, NULL, 'Campaign banner design', '2024-01-16 10:00:00', 1, 'photo', 1, 'https://t.me/marketing_team/2002', 'photo', 0, 0, NULL, 0, '2024-01-16 10:00:00', '2024-01-16 10:00:00'),
(11, 2003, -1001234567891, 456789012, NULL, NULL, '2024-01-16 11:00:00', 1, 'video', 1, 'https://t.me/marketing_team/2003', 'video', 0, 0, NULL, 0, '2024-01-16 11:00:00', '2024-01-16 11:00:00'),
(12, 2004, -1001234567891, 234567890, 'Marketing strategy document', NULL, '2024-01-16 12:00:00', 1, 'document', 1, 'https://t.me/marketing_team/2004', 'document', 0, 0, NULL, 0, '2024-01-16 12:00:00', '2024-01-16 12:00:00'),
(13, 2005, -1001234567891, 456789012, NULL, NULL, '2024-01-16 13:00:00', 0, NULL, 0, 'https://t.me/marketing_team/2005', 'sticker', 1, 0, '💡', 0, '2024-01-16 13:00:00', '2024-01-16 13:00:00'),

-- Group 3: Project Management (2 messages)
(14, 3001, -1001234567892, 123456789, 'Sprint planning meeting scheduled for tomorrow. Agenda: https://docs.example.com/sprint', NULL, '2024-01-17 08:00:00', 0, NULL, 0, 'https://t.me/c/1234567892/3001', 'text', 0, 1, NULL, 0, '2024-01-17 08:00:00', '2024-01-17 08:00:00'),
(15, 3002, -1001234567892, 345678901, 'This message was deleted', NULL, '2024-01-17 09:00:00', 0, NULL, 0, 'https://t.me/c/1234567892/3002', 'text', 0, 0, NULL, 1, '2024-01-17 09:00:00', '2024-01-17 10:00:00');

-- =====================================================
-- 6. REACTIONS (10 reactions)
-- =====================================================
INSERT OR REPLACE INTO reactions (
    id, message_id, group_id, user_id, emoji,
    message_link, reacted_at, created_at
) VALUES 
(1, 1001, -1001234567890, 234567890, '👍', 'https://t.me/techdevs/1001', '2024-01-15 10:31:00', '2024-01-15 10:31:00'),
(2, 1001, -1001234567890, 345678901, '❤️', 'https://t.me/techdevs/1001', '2024-01-15 10:32:00', '2024-01-15 10:32:00'),
(3, 1002, -1001234567890, 123456789, '🔥', 'https://t.me/techdevs/1002', '2024-01-15 11:01:00', '2024-01-15 11:01:00'),
(4, 1002, -1001234567890, 345678901, '👍', 'https://t.me/techdevs/1002', '2024-01-15 11:02:00', '2024-01-15 11:02:00'),
(5, 1007, -1001234567890, 234567890, '🎉', 'https://t.me/techdevs/1007', '2024-01-15 15:01:00', '2024-01-15 15:01:00'),
(6, 1007, -1001234567890, 345678901, '👍', 'https://t.me/techdevs/1007', '2024-01-15 15:02:00', '2024-01-15 15:02:00'),
(7, 2001, -1001234567891, 234567890, '💡', 'https://t.me/marketing_team/2001', '2024-01-16 09:01:00', '2024-01-16 09:01:00'),
(8, 2002, -1001234567891, 456789012, '❤️', 'https://t.me/marketing_team/2002', '2024-01-16 10:01:00', '2024-01-16 10:01:00'),
(9, 2003, -1001234567891, 234567890, '👍', 'https://t.me/marketing_team/2003', '2024-01-16 11:01:00', '2024-01-16 11:01:00'),
(10, 3001, -1001234567892, 345678901, '✅', 'https://t.me/c/1234567892/3001', '2024-01-17 08:01:00', '2024-01-17 08:01:00');

-- =====================================================
-- 7. MEDIA FILES (8 media files)
-- =====================================================
INSERT OR REPLACE INTO media_files (
    id, message_id, file_path, file_name, file_size_bytes,
    file_type, mime_type, thumbnail_path, created_at
) VALUES 
(1, 1002, './downloads/techdevs/1002_photo.jpg', 'ui_design_screenshot.jpg', 245760, 'photo', 'image/jpeg', './downloads/techdevs/1002_photo_thumb.jpg', '2024-01-15 11:00:00'),
(2, 1003, './downloads/techdevs/1003_video.mp4', 'demo_video.mp4', 5242880, 'video', 'video/mp4', './downloads/techdevs/1003_video_thumb.jpg', '2024-01-15 11:30:00'),
(3, 1005, './downloads/techdevs/1005_document.pdf', 'project_documentation.pdf', 1024000, 'document', 'application/pdf', NULL, '2024-01-15 13:00:00'),
(4, 1006, './downloads/techdevs/1006_audio.mp3', 'voice_message.mp3', 512000, 'audio', 'audio/mpeg', NULL, '2024-01-15 14:00:00'),
(5, 2002, './downloads/marketing_team/2002_photo.jpg', 'campaign_banner.jpg', 384000, 'photo', 'image/jpeg', './downloads/marketing_team/2002_photo_thumb.jpg', '2024-01-16 10:00:00'),
(6, 2003, './downloads/marketing_team/2003_video.mp4', 'campaign_video.mp4', 8388608, 'video', 'video/mp4', './downloads/marketing_team/2003_video_thumb.jpg', '2024-01-16 11:00:00'),
(7, 2004, './downloads/marketing_team/2004_document.xlsx', 'marketing_strategy.xlsx', 2048000, 'document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', NULL, '2024-01-16 12:00:00'),
(8, 1002, './downloads/techdevs/1002_photo_alt.jpg', 'ui_design_alternative.jpg', 198000, 'photo', 'image/jpeg', './downloads/techdevs/1002_photo_alt_thumb.jpg', '2024-01-15 11:05:00');

-- =====================================================
-- 8. DELETED MESSAGES (1 deleted message)
-- =====================================================
INSERT OR REPLACE INTO deleted_messages (
    id, message_id, group_id, deleted_at
) VALUES 
(1, 3002, -1001234567892, '2024-01-17 10:00:00');

-- =====================================================
-- 9. DELETED USERS (1 deleted user)
-- =====================================================
INSERT OR REPLACE INTO deleted_users (
    id, user_id, deleted_at
) VALUES 
(1, 567890123, '2024-01-17 10:00:00');

-- =====================================================
-- 10. LOGIN CREDENTIALS (2 records)
-- =====================================================
INSERT OR REPLACE INTO login_credentials (
    id, email, encrypted_password, created_at, updated_at
) VALUES 
(1, 'john.doe@example.com', 'encrypted_password_hash_1', '2024-01-15 10:00:00', '2024-01-20 12:00:00'),
(2, 'jane.smith@example.com', 'encrypted_password_hash_2', '2024-01-16 11:00:00', '2024-01-19 15:00:00');

-- =====================================================
-- 11. USER LICENSE CACHE (2 records)
-- =====================================================
INSERT OR REPLACE INTO user_license_cache (
    id, user_email, license_tier, expiration_date,
    max_devices, max_groups, last_synced, is_active,
    created_at, updated_at
) VALUES 
(1, 'john.doe@example.com', 'gold', '2024-12-31 23:59:59', 2, 5, '2024-01-20 12:00:00', 1, '2024-01-15 10:00:00', '2024-01-20 12:00:00'),
(2, 'jane.smith@example.com', 'premium', '2025-06-30 23:59:59', 3, 10, '2024-01-19 15:00:00', 1, '2024-01-16 11:00:00', '2024-01-19 15:00:00');

-- Re-enable foreign key checks
PRAGMA foreign_keys = ON;

-- =====================================================
-- SUMMARY
-- =====================================================
-- Total Records:
-- - app_settings: 1
-- - telegram_credentials: 2
-- - telegram_groups: 3
-- - telegram_users: 5 (1 deleted)
-- - messages: 15 (various types: text, photo, video, sticker, document, audio, with links)
-- - reactions: 10
-- - media_files: 8
-- - deleted_messages: 1
-- - deleted_users: 1
-- - login_credentials: 2
-- - user_license_cache: 2
-- 
-- Features Demonstrated:
-- ✓ Multiple groups
-- ✓ Multiple users (including deleted user)
-- ✓ Various message types (text, photo, video, sticker, document, audio)
-- ✓ Messages with links
-- ✓ Messages with media
-- ✓ Reactions to messages
-- ✓ Deleted messages tracking
-- ✓ Deleted users tracking
-- ✓ Media file downloads
-- ✓ License tiers (gold, premium)
-- ✓ Telegram credentials
-- ✓ App settings
-- =====================================================

