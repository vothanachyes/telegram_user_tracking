<!-- 01074236-4d16-4ce1-ab03-afce069d4a69 3b55cdc8-47e6-42e2-85c3-fa773dc78542 -->
# Test Data Generator Script Implementation Plan

## Overview

Create `dataRan.py` - a Flet-based UI script that generates comprehensive JSON test data for all application features. Uses Strategy pattern to enable/disable features easily.

## Architecture

### Design Pattern: Strategy Pattern

- **BaseGenerator** (abstract base class) - defines interface for all generators
- **FeatureGenerators** - individual generators for each feature (Groups, Users, Messages, Reactions, Media, Tags, etc.)
- **DataGeneratorOrchestrator** - coordinates all generators and manages dependencies
- **FeatureRegistry** - manages enabled/disabled features

### File Structure

```
dataRan.py (main UI file, ~300-400 lines)
utils/data_generator/
  ├── __init__.py
  ├── base.py (BaseGenerator abstract class)
  ├── orchestrator.py (DataGeneratorOrchestrator)
  ├── registry.py (FeatureRegistry)
  └── generators/
      ├── __init__.py
      ├── group_generator.py
      ├── user_generator.py
      ├── message_generator.py
      ├── reaction_generator.py
      ├── media_generator.py
      ├── tag_generator.py
      ├── deleted_generator.py
      └── settings_generator.py
```

## Implementation Details

### 1. Main UI File: `dataRan.py`

**Location**: Root directory

**Features**:

- Flet-based UI with form inputs
- Date range selector (Year/Month/Custom Date Range)
- Feature checkboxes (Groups, Users, Messages, Reactions, Media, Tags, Deleted Items, Settings)
- Configuration inputs:
  - Number of groups (with random range option)
  - Number of messages per group (with random range)
  - Reactions per message range (min/max)
  - Media percentage (0-100%)
  - Tags per message range (min/max)
  - Deleted items percentage
- Generate button with progress indicator
- Save JSON file dialog

**UI Components**:

- Date range selection (Radio buttons: Year, Month, Custom)
- Date pickers for start/end dates
- Feature checkboxes
- Number inputs with random range toggles
- Progress bar during generation
- Output file path display

### 2. Base Generator (`utils/data_generator/base.py`)

**Abstract base class**:

```python
class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, config: Dict) -> List[Dict]:
        """Generate data based on config"""
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Return list of required feature names"""
```

### 3. Feature Generators (`utils/data_generator/generators/`)

#### GroupGenerator

- Generates `telegram_groups` data
- Fields: group_id, group_name, group_username, last_fetch_date, total_messages
- Realistic group names (e.g., "Tech Developers", "Marketing Team")

#### UserGenerator

- Generates `telegram_users` data
- Fields: user_id, username, first_name, last_name, full_name, phone, bio, profile_photo_path, is_deleted
- Realistic names using faker or predefined lists
- Supports deleted users based on percentage

#### MessageGenerator

- Generates `messages` data
- Fields: message_id, group_id, user_id, content, caption, date_sent, has_media, media_type, message_type, has_sticker, has_link, etc.
- Distributes messages across date range
- Various message types (text, photo, video, sticker, document, audio)
- Realistic message content with optional hashtags
- Links in messages

#### ReactionGenerator

- Generates `reactions` data
- Fields: message_id, group_id, user_id, emoji, reacted_at
- Random emoji selection (👍, ❤️, 🔥, 🎉, etc.)
- Configurable min/max reactions per message

#### MediaGenerator

- Generates `media_files` data
- Fields: message_id, file_path, file_name, file_size_bytes, file_type, mime_type
- Links to messages with has_media=True
- Realistic file names and paths
- Various media types (photo, video, document, audio)

#### TagGenerator

- Generates `message_tags` data
- Fields: message_id, group_id, user_id, tag, date_sent
- Extracts tags from message content (hashtags)
- Configurable min/max tags per message
- Normalized tags (lowercase, no # prefix)

#### DeletedGenerator

- Generates `deleted_messages` and `deleted_users` data
- Based on percentage of messages/users
- Realistic deletion timestamps

#### SettingsGenerator

- Generates `app_settings` data (optional)
- Default configuration values

### 4. Data Generator Orchestrator (`utils/data_generator/orchestrator.py`)

- Manages generation order based on dependencies
- Coordinates all enabled generators
- Ensures referential integrity (user_ids exist, group_ids exist, etc.)
- Distributes data across date range
- Outputs final JSON structure

### 5. Feature Registry (`utils/data_generator/registry.py`)

- Manages enabled/disabled features
- Maps feature names to generator classes
- Dependency resolution

### 6. JSON Output Structure

```json
{
  "metadata": {
    "generated_at": "2024-01-20T10:00:00",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "config": { ... }
  },
  "telegram_groups": [...],
  "telegram_users": [...],
  "messages": [...],
  "reactions": [...],
  "media_files": [...],
  "message_tags": [...],
  "deleted_messages": [...],
  "deleted_users": [...],
  "app_settings": [...]
}
```

## Implementation Steps

1. **Create directory structure** (`data_ran/` with `ui/`, `pattern/`, `script/` subdirectories)
2. **Implement base generator** (`data_ran/pattern/base.py`)
3. **Implement feature registry** (`data_ran/pattern/registry.py`)
4. **Implement AI content generator** (`data_ran/script/ai_generator.py`)
5. **Implement individual generators** (one by one, starting with Groups, then Users, then Messages)

   - Integrate AI generator for Khmer/English content

6. **Implement orchestrator** (`data_ran/pattern/orchestrator.py`) - outputs nested JSON structure
7. **Implement database dumper** (`data_ran/script/db_dumper.py`)
8. **Create main UI** (`data_ran/ui/main_ui.py`)
9. **Create entry point** (`dataRan.py` in root)
10. **Test with various configurations** (JSON export, database dump, both)

## Key Features

- **Strategy Pattern**: Easy to add/remove features by registering/unregistering generators
- **Dependency Management**: Generators declare dependencies (e.g., Messages depend on Groups and Users)
- **Random Ranges**: Support for min/max values for realistic data distribution
- **Date Distribution**: Messages and reactions distributed across date range
- **Referential Integrity**: Ensures all foreign keys reference existing records
- **Realistic Data**: Uses templates and patterns for realistic content

## Dependencies

- `flet` (already in project)
- `faker` (for realistic names) - may need to add to requirements.txt
- `random`, `datetime`, `json` (standard library)

## File Size Compliance

- `dataRan.py`: Target < 400 lines (UI only)
- Each generator: Target < 200 lines
- Orchestrator: Target < 300 lines
- Base/Registry: Target < 150 lines each

### To-dos

- [ ] Create utils/data_generator/ directory structure with __init__.py files and generators/ subdirectory
- [ ] Implement BaseGenerator abstract class in utils/data_generator/base.py with generate() and get_dependencies() methods
- [ ] Implement FeatureRegistry class in utils/data_generator/registry.py to manage enabled/disabled features and generator mapping
- [ ] Implement GroupGenerator in utils/data_generator/generators/group_generator.py to generate telegram_groups data
- [ ] Implement UserGenerator in utils/data_generator/generators/user_generator.py to generate telegram_users data with realistic names
- [ ] Implement MessageGenerator in utils/data_generator/generators/message_generator.py to generate messages with various types, distributed across date range
- [ ] Implement ReactionGenerator in utils/data_generator/generators/reaction_generator.py to generate reactions with random emojis
- [ ] Implement MediaGenerator in utils/data_generator/generators/media_generator.py to generate media_files linked to messages
- [ ] Implement TagGenerator in utils/data_generator/generators/tag_generator.py to extract and generate message_tags from message content
- [ ] Implement DeletedGenerator in utils/data_generator/generators/deleted_generator.py to generate deleted_messages and deleted_users
- [ ] Implement DataGeneratorOrchestrator in utils/data_generator/orchestrator.py to coordinate all generators and manage dependencies
- [ ] Create dataRan.py in root directory with Flet UI for configuration inputs, feature selection, and JSON export