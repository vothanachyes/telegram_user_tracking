# Database Management Commands

This directory contains sample data and fixtures for the Telegram User Tracking application.

## Files

- `demo_data.sql` - Sample database data for testing and development

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

```bash
# Complete reset: clear everything and load sample data
python3 utils/db_commands.py clear-db
python3 utils/db_commands.py init-sample-data

# Backup current data before clearing
python3 utils/db_commands.py dump-data --output backup_$(date +%Y%m%d_%H%M%S).sql
python3 utils/db_commands.py clear-db

# Clear only user content, keep settings and auth
python3 utils/db_commands.py clear-db --preserve-system --preserve-auth
```

