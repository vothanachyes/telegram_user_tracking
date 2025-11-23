<!-- 161aa6f0-2081-41db-a404-f72e1e2e149b 23680824-1113-419b-8ac0-cedaa0677eb1 -->
# Welcome Notification with HTML Template System

## Overview

When a new user is created in the admin app, automatically generate a welcome notification using a beautiful HTML template. The system also supports selecting HTML/MD template files when creating notifications manually.

## Implementation Details

### 1. Create HTML Template File

**File:** `admin/templates/html/new_user_greeting.html`

Create a beautiful, modern HTML card template with:

- Professional card design with gradient backgrounds
- Responsive layout
- Modern typography
- License information section (conditionally displayed)
- Variable placeholders using `{{variable_name}}` syntax
- Impressive visual design to welcome users

**Available variables:**

- `{{user_name}}` - User's display name or email
- `{{user_email}}` - User's email address
- `{{license_tier_name}}` - License tier name (if assigned)
- `{{license_tier_key}}` - License tier key (if assigned)
- `{{license_expiration_date}}` - Formatted expiration date (if available)
- `{{license_max_groups}}` - Maximum groups allowed
- `{{license_max_devices}}` - Maximum devices allowed
- `{{license_max_accounts}}` - Maximum accounts allowed
- `{{app_name}}` - Application name

### 2. Document Template Variables

**File:** `admin/templates/Readme.md`

Create comprehensive documentation including:

- List of all available variables for templates
- Variable descriptions and usage examples
- Template file location and structure
- How to create custom templates
- Variable replacement syntax

### 3. Create Template Loader Utility

**File:** `admin/utils/template_loader.py` (new file)

Create a utility class `TemplateLoader` with methods:

- `load_template(template_path: str) -> str` - Load template file content
- `replace_variables(template_content: str, variables: dict) -> str` - Replace variables in template
- `get_available_templates() -> List[str]` - List all HTML/MD files in templates directory
- Handle file encoding (UTF-8)
- Support both `.html` and `.md` files
- Error handling for missing files or invalid templates

### 4. Add Template Selection to Notification Form Dialog

**File:** `admin/ui/dialogs/notification_form_dialog.py`

Add template selection feature:

- Add dropdown/select field for template files
- List all `.html` and `.md` files from `admin/templates/html/` directory
- Add "None" option for manual content entry
- When template is selected:
- Load template content
- Show preview or load into content field
- Allow editing after loading
- Add button to "Load Template" that populates content field
- Keep existing manual content entry as fallback

**UI Changes:**

- Add template dropdown before content field
- Add "Load Template" button next to dropdown
- When template loaded, populate content_field with template content
- User can still edit content after loading template

### 5. Update Welcome Notification Method

**File:** `admin/services/admin_notification_service.py`

Add `create_welcome_notification()` method that:

- Uses `TemplateLoader` to load `new_user_greeting.html`
- Builds variables dictionary from user data and license info
- Replaces variables in template
- Creates notification with processed HTML content
- Handles missing template gracefully (fallback to simple text)

**Variable building:**

- Get user display name or email
- If license exists, get tier definition and license data
- Format expiration date nicely
- Build complete variables dict
- Pass to template loader

### 6. Update User Creation Handler

**File:** `admin/ui/pages/users_page.py`

Modify `_handle_create_user()` method to:

- After successful user creation and license assignment (if any)
- Call `admin_notification_service.create_welcome_notification()` with:
- User UID
- Email
- Display name
- License tier (if one was created)
- Log success/failure but don't block user creation if notification fails
- Handle errors gracefully (notification failure shouldn't prevent user creation)

**Location:** After line 198 (after license creation) and before reloading users

## Files to Create/Modify

1. **New:** `admin/templates/html/new_user_greeting.html` - Beautiful HTML template
2. **Update:** `admin/templates/Readme.md` - Document available variables
3. **New:** `admin/utils/template_loader.py` - Template loading utility
4. **Update:** `admin/services/admin_notification_service.py` - Add welcome notification method
5. **Update:** `admin/ui/dialogs/notification_form_dialog.py` - Add template selection
6. **Update:** `admin/ui/pages/users_page.py` - Call welcome notification on user creation

## Template Variable Reference

Variables available in templates (documented in Readme.md):

- `{{user_name}}` - User display name or email
- `{{user_email}}` - User email address
- `{{user_uid}}` - User UID
- `{{license_tier_name}}` - License tier display name
- `{{license_tier_key}}` - License tier key
- `{{license_expiration_date}}` - Formatted expiration date
- `{{license_max_groups}}` - Max groups limit
- `{{license_max_devices}}` - Max devices limit
- `{{license_max_accounts}}` - Max accounts limit
- `{{app_name}}` - Application name
- `{{current_date}}` - Current date (formatted)

## Error Handling

- Template file missing: Log warning, use fallback simple text notification
- Template loading errors: Log error, fallback to simple text
- Variable replacement errors: Log error, leave variables as-is or use defaults
- Notification creation failure: Log but don't block user creation
- Missing license info: Template should handle gracefully with conditional sections

## Testing Considerations

- Test welcome notification with template
- Test welcome notification without license
- Test welcome notification with license
- Test template selection in notification dialog
- Test loading different template files
- Test variable replacement with various data
- Test error handling (missing template, invalid variables)
- Verify HTML renders correctly in notification detail view

### To-dos

- [ ] Add create_welcome_notification() method to AdminNotificationService that generates welcome notification with user info and license details
- [ ] Update _handle_create_user() in users_page.py to call welcome notification after successful user and license creation