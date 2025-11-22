# Admin Interface

Modern admin interface for managing Firebase users, licenses, and app updates.

## Features

- **User Management**: View, create, edit, and delete Firebase users
- **License Management**: Manage user licenses (tiers, expiration, limits)
- **App Updates**: Update app version information and download URLs
- **Device Management**: View and manage user devices
- **Analytics Dashboard**: View statistics about users, licenses, and devices
- **Export Reports**: Export users and licenses to Excel, analytics to PDF

## Requirements

- Python 3.10+
- Firebase Admin SDK credentials file
- Required packages (see `requirements.txt` in project root)

## Setup

1. **Firebase Credentials**:
   - Place your Firebase Admin SDK credentials JSON file in the `config/` directory
   - Or set the `FIREBASE_CREDENTIALS_PATH` environment variable to point to the file

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Admin Interface**:
   ```bash
   python admin/main.py
   ```

## Usage

### Login

- Use your Firebase Auth email and password to log in
- The admin interface uses separate authentication from the main app
- Session timeout: 60 minutes of inactivity

### Navigation

- **Dashboard**: View analytics and statistics
- **Users**: Manage Firebase users (CRUD operations)
- **Licenses**: Manage user licenses (CRUD operations)
- **App Updates**: Update app version information
- **Devices**: View and manage user devices
- **Activity Logs**: View activity logs (to be implemented)
- **Bulk Operations**: Perform bulk operations (to be implemented)

### User Management

- View all users in a searchable, paginated table
- Create new users with email and password
- Edit user properties (email, display name, disabled status)
- Delete users (with confirmation)
- View user licenses and devices

### License Management

- View all licenses in a searchable, paginated table
- Create new licenses for users
- Edit license properties (tier, expiration, limits)
- Delete licenses (with confirmation)
- View license statistics

### App Updates

- Update app version information
- Set download URLs for Windows, macOS, and Linux
- Add release notes
- Enable/disable updates

## Security

- Admin interface is separate from the main app
- Uses Firebase Admin SDK for all operations
- Credentials file should NOT be committed to git
- All delete operations require confirmation
- Session timeout after inactivity

## Build Exclusion

The `admin/` directory is automatically excluded from the main app build (see `scripts/build.py`).

## Development

The admin interface shares the same `.venv` as the main app but may require additional dependencies:

- `firebase-admin>=6.2.0` - For Firebase Admin SDK operations
- `pandas` - For Excel export
- `openpyxl` - For Excel file generation
- `reportlab` - For PDF export

## Notes

- Dark mode only, English only
- Some features (dialogs, activity logs, bulk operations) are placeholders for future implementation
- Follow repository file size limits (services < 300 lines, pages < 250 lines, components < 200 lines)

