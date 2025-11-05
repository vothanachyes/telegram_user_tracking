# Quick Start Guide

## Installation

1. **Create and activate virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Create .env file:**

```bash
# Copy example and edit
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Firebase Configuration (Optional - can run without it)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id

# Application Settings
APP_NAME=Telegram User Tracking
APP_VERSION=1.0.0
DEVELOPER_NAME=Your Name
DEVELOPER_EMAIL=your.email@example.com
DEVELOPER_CONTACT=+1234567890

# Default Paths
DEFAULT_DOWNLOAD_DIR=./downloads
DATABASE_PATH=./data/app.db

# Theme
PRIMARY_COLOR=#082f49
```

## Running the Application

### Development Mode

```bash
python main.py
```

The application will start and open a window. If Firebase is not configured, it will skip the login screen and go directly to the dashboard.

## First Time Setup

### 1. Configure Settings

1. Click the **Settings** icon in the sidebar (gear icon)
2. Configure the following:

**Appearance:**
- Choose Dark/Light mode
- Select language (English/Khmer)
- Adjust corner radius for UI elements

**Telegram Authentication:**
- Get your API credentials from https://my.telegram.org/apps
- Enter your **API ID** and **API Hash**
- Save settings

**Fetch Settings:**
- Set download directory path
- Configure max file size for downloads
- Set fetch delay (to avoid Telegram rate limits)
- Choose which media types to download

### 2. Connect to Telegram

To fetch messages from Telegram groups, you need to authenticate your Telegram account:

1. The app will use Pyrogram for Telegram authentication
2. When fetching for the first time, you'll be prompted for:
   - Your phone number
   - OTP code (sent to your Telegram)
   - 2FA password (if enabled)

### 3. Fetch Messages

1. Go to the **Telegram** page (telegram icon in sidebar)
2. Click on the **Messages** tab
3. The first time, you'll need to input a group ID to fetch from
4. Select date range for fetching
5. Click **Fetch Messages** button
6. Wait for the process to complete

## Features Overview

### Dashboard
- View total messages, users, and groups
- See media storage usage
- Monitor today's and monthly statistics
- View recent activity feed

### Telegram Page

**Messages Tab:**
- View all fetched messages in a table
- Filter by group and date range
- Search messages
- Export to Excel or PDF
- Click rows for details

**Users Tab:**
- View all users from fetched groups
- See user information (name, phone, bio)
- Export user lists
- Manage user profiles

### Settings Page
- Customize appearance
- Configure Telegram API
- Manage fetch settings
- Adjust media download options

### Profile Page
- View current user info
- See app version and developer info
- Logout (if using Firebase auth)

## Folder Structure

Downloaded media is organized as:
```
downloads/
├── {group_id}/
│   ├── {username}/
│   │   ├── {date}/
│   │   │   ├── {message_id}_{time}/
│   │   │   │   ├── photo.jpg
│   │   │   │   ├── video.mp4
│   │   │   │   └── caption.txt
```

## Building Executable

To create a standalone executable:

```bash
python build.py
```

The executable will be created in the `dist/` directory.

## Troubleshooting

### Firebase Not Working
- The app can run without Firebase
- Login screen will be skipped
- All features except multi-device enforcement will work

### Telegram Connection Issues
- Make sure API ID and API Hash are correct
- Check your internet connection
- Verify phone number format (+1234567890)

### Media Not Downloading
- Check download directory permissions
- Verify max file size settings
- Ensure media type is enabled in settings

### Database Issues
- Database is created automatically in `data/app.db`
- To reset, delete the `data/` folder (will lose all data)

## Tips

1. **Rate Limiting:** Set fetch delay to 1-2 seconds to avoid Telegram blocks
2. **Storage:** Monitor media storage on dashboard
3. **Backup:** Regularly backup the `data/` folder
4. **Performance:** Use filters and date ranges for better performance
5. **Export:** Use Excel for full data, PDF for reports (limited to 100 rows)

## Support

For issues or questions:
- Email: ${DEVELOPER_EMAIL}
- Phone: ${DEVELOPER_CONTACT}

## License

MIT License

