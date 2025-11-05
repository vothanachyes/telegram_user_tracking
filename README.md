# Telegram User Tracking Desktop Application

A modern cross-platform desktop application for tracking and managing Telegram group reports with advanced filtering, search, and export capabilities.

## Features

- 🔐 **Firebase Authentication** - Secure login with single-device enforcement
- 📊 **Dashboard** - Comprehensive statistics and activity tracking
- 💬 **Telegram Integration** - Fetch messages and media from Telegram groups via Pyrogram
- 🗂️ **Data Management** - Searchable tables for messages and users with CRUD operations
- 📁 **Media Management** - Automatic download and organization of media files
- 📤 **Export** - Generate PDF and Excel reports
- 🎨 **Customizable UI** - Dark/Light mode, adjustable corner radius
- 🌐 **Bilingual** - English and Khmer language support
- 💾 **Offline Storage** - Local SQLite database for fast access

## Technology Stack

- **Python 3.10+**
- **Flet** - Cross-platform UI framework
- **SQLite** - Local database
- **Pyrogram** - Telegram API client
- **Firebase Admin SDK** - Authentication
- **Pandas** - Data manipulation
- **xlsxwriter** - Excel export
- **ReportLab** - PDF generation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram_user_tracking
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Firebase credentials and settings
```

5. Run the application:
```bash
python main.py
```

## Configuration

### Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Email/Password authentication
3. Download the service account credentials JSON file
4. Update the `.env` file with the path to your credentials file

### Telegram API Setup

1. Visit [Telegram API Development Tools](https://my.telegram.org/apps)
2. Create a new application to get your API ID and API Hash
3. Enter these credentials in the application's Settings page

## Building Executable

Build the application for your platform:

```bash
python build.py
```

The executable will be created in the `dist/` directory.

## Usage

1. **Login** - Authenticate with your Firebase email and password
2. **Configure Settings** - Set up Telegram API credentials and fetch preferences
3. **Connect Telegram** - Authenticate your Telegram account
4. **Fetch Messages** - Select a group and date range to fetch messages
5. **View & Manage** - Browse, search, filter, and export data
6. **Dashboard** - Monitor statistics and activity

## Project Structure

```
user_tracking/
├── main.py                  # Application entry point
├── config/                  # Configuration management
├── database/                # Database models and operations
├── services/                # Business logic (auth, telegram, export)
├── ui/                      # User interface (pages, components, dialogs)
├── utils/                   # Helper functions and validators
└── assets/                  # Icons and images
```

## License

MIT License

## Developer Contact

- **Name**: [Your Name]
- **Email**: [your.email@example.com]
- **Phone**: [+1234567890]

## Version

1.0.0

