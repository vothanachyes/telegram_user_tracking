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
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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
python3 main.py
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

### Logging Configuration

The application provides configurable logging filters to reduce console noise:

- **`FLET_DEBUG_LOGS_ENABLED`** - Set to `true` to show Flet framework DEBUG logs (default: `false`)
- **`VERBOSE_HTTP_LOGS_ENABLED`** - Set to `true` to show verbose HTTP/2 DEBUG logs from `hpack`, `httpcore`, `httpx`, and `h2` loggers (default: `false`)

By default, verbose DEBUG logs are filtered out from the console to show only important logs. All logs are still written to log files for debugging purposes. Enable these flags in your `.env` file when debugging specific issues:

```bash
FLET_DEBUG_LOGS_ENABLED=true
VERBOSE_HTTP_LOGS_ENABLED=true
```

## Building Executable

### Local Build

Build the application for your current platform:

```bash
python3 scripts/build.py
```

The executable will be created in the `dist/` directory.

### Windows Build from macOS/Linux

Since PyInstaller cannot cross-compile, use **GitHub Actions** to build Windows executables from any platform:

1. **Manual Trigger**: Go to GitHub Actions tab → "Build Windows Executable" → "Run workflow"
2. **Automatic Trigger**: Push a version tag (e.g., `git tag v1.0.0 && git push origin v1.0.0`)
3. **Download**: After build completes, download the `.exe` from the Artifacts section

📖 **See detailed guide**: [Windows Build Workflow Documentation](docs/WINDOWS_BUILD_WORKFLOW.md)

## Testing

Run the test suite using pytest:

```bash
pytest tests/
```

This will run all unit and integration tests for login and licensing functionality. The test suite includes:

- **Unit Tests** - Tests for `AuthService` and `LicenseService` with mocked dependencies
- **Integration Tests** - End-to-end tests for login flow and licensing enforcement

To run specific test suites:

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_auth_service.py
```

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

