# Telegram Group Exporter

A simple, runnable script to export files and messages from Telegram groups using Telethon.

## Features

- ✅ Export files (documents, photos, videos, audio) from Telegram groups
- ✅ Extract message metadata (sender, date, caption, links)
- ✅ Organize files by user and date
- ✅ Progress tracking with tqdm
- ✅ Rate limiting to avoid API limits
- ✅ Retry mechanism for failed downloads
- ✅ File size limits
- ✅ Date range filtering
- ✅ Comprehensive logging

## Setup

### 1. Create Virtual Environment

```bash
cd z_sanbox/telethon
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

Edit `config.py` or create a `.env` file with your settings:

```env
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=+1234567890
GROUP_ID=-1234567890
EXPORT_FOLDER=/path/to/export
MAX_FILE_SIZE_MB=500
RATE_LIMIT=2
MAX_RETRIES=3
```

Or modify the values directly in `config.py`.

## Usage

### Basic Usage

```bash
python main.py
```

The script will:
1. Connect to Telegram using your credentials
2. Validate configuration
3. Ask for confirmation
4. Export files and messages from the specified group
5. Save everything to the export folder organized by user and date

### Export Folder Structure

```
EXPORT_FOLDER/
├── username1/
│   ├── 2025-04-28/
│   │   ├── file1.pdf
│   │   ├── meta_123.json
│   │   └── ...
│   └── 2025-04-29/
│       └── ...
└── username2/
    └── ...
```

### Metadata Format

Each message gets a `meta_{message_id}.json` file with:

```json
{
  "sender_id": 123456789,
  "sender_name": "username",
  "message_id": 123,
  "date": "2025-04-28T10:30:00",
  "caption": "Message text",
  "links": ["https://example.com"],
  "file_size_mb": 2.5,
  "file_type": "application/pdf",
  "file_path": "document.pdf"
}
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `API_ID` | Telegram API ID | Required |
| `API_HASH` | Telegram API Hash | Required |
| `PHONE_NUMBER` | Your phone number | Required |
| `GROUP_ID` | Target group ID | Required |
| `EXPORT_FOLDER` | Export destination | Required |
| `MAX_FILE_SIZE_MB` | Maximum file size to download | 500 |
| `RATE_LIMIT` | Seconds between downloads | 2 |
| `MAX_RETRIES` | Retry attempts for failed downloads | 3 |
| `START_DATE` | Start date for export | Required |
| `END_DATE` | End date for export | Required |
| `SESSION_NAME` | Session file name | "user_session" |

## Logging

Logs are written to:
- Console (stdout)
- `exporter.log` file

## Error Handling

- **FloodWaitError**: Automatically waits and retries
- **File size limits**: Skips files exceeding `MAX_FILE_SIZE_MB`
- **Network errors**: Retries up to `MAX_RETRIES` times
- **Invalid files**: Logs warning and continues

## Notes

- First run will require phone verification code
- Session file (`.session`) is saved for future runs
- Large exports may take significant time
- Ensure sufficient disk space
- Respect Telegram's rate limits

## Troubleshooting

### "API_ID and API_HASH must be set"
- Set these in `config.py` or `.env` file

### "Flood wait" errors
- Increase `RATE_LIMIT` in config
- Wait for the specified time

### Files not downloading
- Check file size limits
- Verify group permissions
- Check network connection

### Session expired
- Delete `.session` file and re-authenticate

## License

Internal use only.

