# Test Data Generator (dataRan)

A comprehensive test data generator for the Telegram User Tracking application. Generate realistic test data in JSON format or directly insert into the database with support for Khmer and English content.

## Features

- **Flexible Date Ranges**: Generate data for 1 year, 1 month, or custom date ranges
- **Feature Toggle**: Enable/disable specific features (groups, users, messages, reactions, media, tags, deleted items, settings)
- **Multi-language Support**: Generate content in Khmer, English, or both languages
- **Realistic Data**: AI-powered content generation for names, messages, and group names
- **Random Ranges**: Support for random ranges for groups, messages, reactions, media, and tags
- **Multiple Output Formats**: 
  - JSON file export (nested structure)
  - Direct database dump
  - Both options simultaneously
- **Strategy Pattern**: Easy to add or disable features without modifying core code

## Installation

The data generator is part of the main project. No additional installation is required beyond the project dependencies.

## Usage

### Running the Application

```bash
python dataRan.py
```

This will launch a Flet-based GUI where you can configure and generate test data.

### Command Line Usage (Future)

```bash
# Generate JSON file only
python dataRan.py --json --output test_data.json

# Generate and dump to database
python dataRan.py --db --db-path ./data/app.db

# Generate both JSON and database dump
python dataRan.py --json --db --output test_data.json --db-path ./data/app.db
```

## UI Configuration

### Date Range Selection

- **1 Year**: Generates data for the past 365 days
- **1 Month**: Generates data for the past 30 days
- **Custom Range**: Select specific start and end dates

### Feature Selection

Enable or disable any of the following features:

- **Groups**: Telegram groups
- **Users**: Telegram users (with Khmer/English names)
- **Messages**: Messages with various types (text, photo, video, sticker, document, audio)
- **Reactions**: Emoji reactions to messages
- **Media Files**: Media files linked to messages
- **Tags**: Hashtags extracted from message content
- **Deleted Items**: Deleted messages and users
- **App Settings**: Application settings

### Language Selection

- **Khmer**: Generate Khmer names, messages, and group names
- **English**: Generate English names, messages, and group names
- **Both**: Mix of Khmer and English content

### Configuration Options

#### Groups
- **Number of Groups**: Fixed number or random range (min/max)
- **Random Range**: Toggle to use random range instead of fixed number

#### Users
- **Number of Users**: Total number of users to generate
- **Deleted Percentage**: Percentage of users to mark as deleted

#### Messages
- **Messages per Group**: Fixed number or random range (min/max)
- **Random Range**: Toggle to use random range instead of fixed number
- **Media Percentage**: Percentage of messages that include media (0-100)

#### Reactions
- **Min Reactions**: Minimum reactions per message
- **Max Reactions**: Maximum reactions per message

#### Tags
- **Min Tags**: Minimum hashtags per message
- **Max Tags**: Maximum hashtags per message

#### Deleted Items
- **Deleted Percentage**: Percentage of messages/users to mark as deleted (0-100)

### Output Options

#### JSON File
- **Generate JSON File**: Export data to JSON file
- File picker dialog will appear to select save location

#### Database Dump
- **Direct Database Dump**: Insert data directly into database
- **Database Path**: Path to database file (default: `./data/app.db`)
- **Clear Database First**: Option to clear existing data before insertion

## Generated Data Structure

### Nested JSON Structure

The generator creates a nested JSON structure that reflects the relationships between entities:

```json
{
  "metadata": {
    "generated_at": "2024-01-20T10:00:00",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "config": {
      "num_groups": 3,
      "num_users": 10,
      "num_messages": 150,
      "num_reactions": 75,
      "num_media_files": 45,
      "num_tags": 120,
      "languages": ["khmer", "english"]
    }
  },
  "telegram_groups": [
    {
      "group_id": -1001234567890,
      "group_name": "Tech Developers",
      "group_username": "techdevs_123",
      "last_fetch_date": "2024-12-31T23:59:59",
      "total_messages": 50,
      "users": [
        {
          "user_id": 123456789,
          "username": "john_doe_123",
          "first_name": "John",
          "last_name": "Doe",
          "full_name": "John Doe",
          "messages": [
            {
              "message_id": 1001,
              "content": "Hello world #test #development",
              "date_sent": "2024-01-15T10:30:00",
              "reactions": [
                {
                  "user_id": 234567890,
                  "emoji": "👍",
                  "reacted_at": "2024-01-15T10:31:00"
                }
              ],
              "media_files": [],
              "tags": ["test", "development"]
            }
          ]
        }
      ]
    }
  ],
  "app_settings": {
    "theme": "dark",
    "language": "en",
    ...
  },
  "_flat_data": {
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
}
```

### Flat Data Structure

The `_flat_data` section contains flat lists of all entities, suitable for database import or programmatic processing.

## Architecture

### Design Pattern: Strategy Pattern

The generator uses the Strategy pattern to make it easy to add or disable features:

- **BaseGenerator**: Abstract base class defining the interface for all generators
- **FeatureGenerators**: Individual generators for each feature type
- **FeatureRegistry**: Manages enabled/disabled features and generator mapping
- **DataGeneratorOrchestrator**: Coordinates all generators and manages dependencies

### Directory Structure

```
data_ran/
├── __init__.py
├── README.md
├── ui/
│   ├── __init__.py
│   └── main_ui.py          # Flet UI components
├── pattern/
│   ├── __init__.py
│   ├── base.py             # BaseGenerator abstract class
│   ├── registry.py         # FeatureRegistry
│   └── orchestrator.py     # DataGeneratorOrchestrator
└── script/
    ├── __init__.py
    ├── ai_generator.py     # AI content generation
    ├── db_dumper.py        # Database dump functionality
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

## Adding New Features

To add a new feature generator:

1. Create a new generator class in `data_ran/script/generators/` that inherits from `BaseGenerator`
2. Implement the `generate()` method
3. Implement the `get_dependencies()` method to specify required features
4. Register the generator in `main_ui.py`:
   ```python
   self.registry.register('feature_name', FeatureGenerator)
   ```
5. Add a checkbox in the UI for the new feature

Example:

```python
from data_ran.pattern.base import BaseGenerator

class MyFeatureGenerator(BaseGenerator):
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Generate data based on config
        return []
    
    def get_dependencies(self) -> List[str]:
        return ['groups', 'users']  # Dependencies
```

## Examples

### Example 1: Generate 1 Month of Data

1. Select "1 Month" date range
2. Enable: Groups, Users, Messages, Reactions, Tags
3. Set: 3 groups, 10 users, 100 messages per group
4. Languages: English
5. Output: JSON file only
6. Click "Generate Data"

### Example 2: Generate Full Year with Database Dump

1. Select "1 Year" date range
2. Enable all features
3. Set: 5 groups (random 3-7), 20 users, 200 messages per group (random 100-300)
4. Languages: Khmer and English
5. Output: Both JSON and database dump
6. Database path: `./data/app.db`
7. Clear database first: Yes
8. Click "Generate Data"

### Example 3: Custom Date Range

1. Select "Custom Range"
2. Choose start date: 2024-01-01
3. Choose end date: 2024-06-30
4. Configure features as needed
5. Generate data

## Data Generation Details

### Message Types

The generator creates various message types:
- **Text**: Regular text messages with optional hashtags
- **Photo**: Messages with photo media
- **Video**: Messages with video media
- **Sticker**: Sticker messages with emoji
- **Document**: Messages with document attachments
- **Audio**: Messages with audio files

### Content Generation

- **Khmer Names**: Realistic Khmer first and last names
- **English Names**: Common English first and last names
- **Messages**: Context-appropriate messages in selected languages
- **Group Names**: Realistic group names in selected languages
- **Hashtags**: Relevant hashtags extracted from message content

### Date Distribution

Messages are distributed randomly across the selected date range to simulate realistic activity patterns.

## Troubleshooting

### Database Dump Fails

- Ensure the database path is correct
- Check that the database file exists or can be created
- Verify foreign key constraints are satisfied
- Check database permissions

### JSON File Not Saving

- Ensure you have write permissions in the selected directory
- Check available disk space
- Verify the file path is valid

### Generation Takes Too Long

- Reduce the number of groups, users, or messages
- Disable features you don't need
- Use smaller date ranges

### Missing Dependencies

If you see dependency errors:
- Ensure all required features are enabled
- Check that generators are registered correctly
- Verify the generation order in the orchestrator

## Future Enhancements

- Command-line interface (CLI) support
- Batch generation with multiple configurations
- Template-based generation
- Export to other formats (CSV, Excel)
- Integration with external AI APIs for more realistic content
- Performance optimizations for large datasets
- Progress tracking for long-running generations

## License

Part of the Telegram User Tracking application.

## Support

For issues or questions, please refer to the main project documentation or create an issue in the project repository.

