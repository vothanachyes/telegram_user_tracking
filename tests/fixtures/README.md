# Database Management Commands

This directory contains sample data and fixtures for the Telegram User Tracking application.

## Files

- `demo_data.sql` - Sample database data for testing and development
- `db_fixtures.py` - Database fixtures for testing

## Demo Data Overview

The `demo_data.sql` file contains comprehensive sample data demonstrating all features of the application:

### Data Included

- **3 Telegram Groups**: Tech Developers Community, Marketing Team, Project Management
- **5 Telegram Users**: Including 1 deleted user
- **15 Messages**: Various types (text, photo, video, sticker, document, audio) with links and media
- **23 Message Tags**: Hashtags extracted from message content and captions (e.g., #python, #design, #campaign)
- **10 Reactions**: Various emoji reactions to messages
- **8 Media Files**: Photos, videos, documents, and audio files
- **1 Deleted Message**: Demonstrating soft delete tracking
- **1 Deleted User**: Demonstrating user deletion tracking
- **2 Login Credentials**: Sample user accounts
- **2 License Records**: Gold and premium tier examples
- **2 Telegram Credentials**: Sample session data
- **1 App Settings**: Default application configuration

### Tag Feature

The demo data includes **23 message tags** extracted from hashtags in messages. Tags are normalized (lowercase, without # prefix) and stored in the `message_tags` table. Examples include:

- **Tech Group**: `python`, `library`, `opensource`, `design`, `ui`, `ux`, `documentation`, `project`, `team`, `success`, `celebration`
- **Marketing Group**: `campaign`, `launch`, `marketing`, `design`, `banner`, `strategy`, `planning`
- **Project Management Group**: `sprint`, `meeting`, `planning`

Tags can be used for filtering messages, analytics, and autocomplete suggestions in the UI.

## How to Run Demo Data

### Quick Start

The easiest way to load the demo data into your database:

```bash
# Load demo data (default location: tests/fixtures/demo_data.sql)
python3 -m utils.db_commands init-sample-data
```

This will:
1. Read the SQL file from `tests/fixtures/demo_data.sql`
2. Execute all INSERT statements
3. Load all sample data including tags, messages, users, groups, etc.

### Complete Reset (Recommended for First Time)

If you want to start fresh with demo data:

```bash
# Clear all existing data
python3 -m utils.db_commands clear-db

# Load demo data
python3 -m utils.db_commands init-sample-data
```

### Using Custom SQL File

```bash
# Load from a custom SQL file
python3 -m utils.db_commands init-sample-data --sql-file path/to/your/data.sql
```

### Using Custom Database Path

```bash
# Specify a custom database path
python3 -m utils.db_commands init-sample-data --db-path ./custom/path/app.db
```

## Usage

The database management commands are available via `utils/db_commands.py`:

### 1. Clear Database Data

Clear all or selected data from the database:

```bash
# Clear all data (including system and auth)
python3 utils/db_commands.py clear-db

# Clear only user data (preserve system and auth)
python3 utils/db_commands.py clear-db --preserve-system --preserve-auth

# Clear only user content (preserve system, auth, and credentials)
python3 utils/db_commands.py clear-db --preserve-system --preserve-auth
```

**Options:**
- `--preserve-system` - Preserve `app_settings` table (system configuration)
- `--preserve-auth` - Preserve auth-related tables (`login_credentials`, `user_license_cache`, `telegram_credentials`)

### 2. Initialize Sample Data

Load sample data from SQL file:

```bash
# Load default sample data
python3 utils/db_commands.py init-sample-data

# Load from custom SQL file
python3 utils/db_commands.py init-sample-data --sql-file path/to/data.sql
```

**Options:**
- `--sql-file` - Path to SQL file (default: `tests/fixtures/demo_data.sql`)

### 3. Dump Database Data

Export current database data to SQL file:

```bash
# Dump all data to default location
python3 utils/db_commands.py dump-data

# Dump to custom file
python3 utils/db_commands.py dump-data --output path/to/output.sql

# Dump without system or auth data
python3 utils/db_commands.py dump-data --exclude-system --exclude-auth
```

**Options:**
- `--output` - Path to output SQL file (default: `tests/fixtures/demo_data.sql`)
- `--exclude-system` - Exclude `app_settings` table from dump
- `--exclude-auth` - Exclude auth-related tables from dump

### Common Options

All commands support:
- `--db-path` - Custom database path (default: from `DATABASE_PATH` env var or `./data/app.db`)

## Table Categories

The commands categorize tables as follows:

- **System Tables**: `app_settings` (application configuration)
- **Auth Tables**: `login_credentials`, `user_license_cache`, `telegram_credentials` (authentication and licensing)
- **User Data Tables**: `telegram_groups`, `telegram_users`, `messages`, `reactions`, `media_files`, `deleted_messages`, `deleted_users` (user content)

## Examples

### Loading Demo Data

```bash
# Complete reset: clear everything and load sample data
python3 -m utils.db_commands clear-db
python3 -m utils.db_commands init-sample-data

# Load demo data without clearing (will merge/overwrite existing data)
python3 -m utils.db_commands init-sample-data
```

### Backup and Restore

```bash
# Backup current data before clearing
python3 -m utils.db_commands dump-data --output backup_$(date +%Y%m%d_%H%M%S).sql
python3 -m utils.db_commands clear-db

# Restore from backup
python3 -m utils.db_commands init-sample-data --sql-file backup_20240120_120000.sql
```

### Selective Clearing

```bash
# Clear only user content, keep settings and auth
python3 -m utils.db_commands clear-db --preserve-system --preserve-auth

# Then load demo data
python3 -m utils.db_commands init-sample-data
```

## Verifying Demo Data

After loading the demo data, you can verify it was loaded correctly:

```bash
# Using sqlite3 CLI (if installed)
sqlite3 data/app.db "SELECT COUNT(*) FROM messages;"
sqlite3 data/app.db "SELECT COUNT(*) FROM message_tags;"
sqlite3 data/app.db "SELECT tag, COUNT(*) as count FROM message_tags GROUP BY tag ORDER BY count DESC;"
```

Expected results:
- Messages: 15
- Message Tags: 23
- Unique Tags: ~15-20 (some tags appear in multiple messages)

## Troubleshooting

### Database File Not Found

If you get an error about the database file not existing:

1. Make sure the database has been initialized by running the application at least once
2. Or manually create the database directory: `mkdir -p data`
3. The database will be created automatically when you run the application

### Foreign Key Constraint Errors

If you encounter foreign key errors:

1. Make sure you're loading the complete SQL file (it includes all tables)
2. The SQL file disables foreign key checks temporarily during loading
3. If issues persist, try clearing the database first: `python3 -m utils.db_commands clear-db`

### Tags Not Appearing

If tags don't appear in the UI:

1. Verify tags were loaded: `sqlite3 data/app.db "SELECT * FROM message_tags LIMIT 5;"`
2. Check that the tag feature is enabled in the application
3. Tags are normalized (lowercase, no # prefix) in the database

