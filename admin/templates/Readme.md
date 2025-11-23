# Notification Template System

This directory contains HTML and Markdown templates for notification content. Templates support variable replacement using `{{variable_name}}` syntax.

## Template Location

Templates should be placed in:
- `admin/templates/html/` - For HTML templates (`.html` files)
- `admin/templates/md/` - For Markdown templates (`.md` files)

## Variable Syntax

Variables in templates use double curly braces: `{{variable_name}}`

Example:
```html
<p>Welcome, {{user_name}}!</p>
<p>Your email is {{user_email}}</p>
```

## Available Variables

### User Information Variables

- **`{{user_name}}`** - User's display name, or email if display name is not set
- **`{{user_email}}`** - User's email address
- **`{{user_uid}}`** - User's unique identifier (UID)

### License Information Variables

These variables are only available when a license is assigned to the user:

- **`{{license_tier_name}}`** - License tier display name (e.g., "Premium", "Enterprise")
- **`{{license_tier_key}}`** - License tier key/identifier (e.g., "premium", "enterprise")
- **`{{license_expiration_date}}`** - Formatted expiration date (e.g., "December 31, 2024")
- **`{{license_max_groups}}`** - Maximum number of groups allowed (-1 for unlimited)
- **`{{license_max_devices}}`** - Maximum number of devices allowed (-1 for unlimited)
- **`{{license_max_accounts}}`** - Maximum number of accounts allowed (-1 for unlimited)

### Application Variables

- **`{{app_name}}`** - Application name (default: "Telegram User Tracking")
- **`{{current_date}}`** - Current date formatted as "Month Day, Year" (e.g., "January 15, 2024")

### Special Variables

- **`{{license_section}}`** - Pre-formatted HTML section containing license information. This is automatically generated when a license exists. If no license is assigned, this variable will be empty.

### Deletion Warning Template Variables

For the `user_deletion_warning.html` template:

- **`{{deletion_date}}`** - Formatted deletion date (e.g., "January 15, 2024")
- **`{{deletion_time}}`** - Formatted deletion time (e.g., "02:30 PM UTC")

## Creating Custom Templates

### Step 1: Create Template File

Create a new `.html` or `.md` file in the appropriate templates directory:

```
admin/templates/html/my_custom_template.html
```

### Step 2: Use Variables

Add variables using `{{variable_name}}` syntax:

```html
<div>
    <h1>Hello, {{user_name}}!</h1>
    <p>Welcome to {{app_name}}.</p>
    {{license_section}}
</div>
```

### Step 3: Use in Notifications

When creating a notification in the admin app:
1. Select your template from the "Template" dropdown
2. Click "Load Template" to populate the content field
3. Edit the content if needed
4. Variables will be automatically replaced when the notification is sent

## Template Examples

### Simple Welcome Template

```html
<h1>Welcome, {{user_name}}!</h1>
<p>Thank you for joining {{app_name}}.</p>
<p>Your account email: {{user_email}}</p>
```

### License Information Template

```html
<div>
    <h2>Your License Details</h2>
    <p><strong>Tier:</strong> {{license_tier_name}}</p>
    <p><strong>Expires:</strong> {{license_expiration_date}}</p>
    <ul>
        <li>Max Groups: {{license_max_groups}}</li>
        <li>Max Devices: {{license_max_devices}}</li>
        <li>Max Accounts: {{license_max_accounts}}</li>
    </ul>
</div>
```

## Variable Replacement

When a template is loaded and variables are replaced:

1. **Missing variables** - If a variable is not provided, it will remain as `{{variable_name}}` in the output
2. **Empty values** - If a variable has an empty value, it will be replaced with an empty string
3. **Special handling** - The `{{license_section}}` variable is automatically generated and includes conditional formatting

## Best Practices

1. **Always provide fallbacks** - Use default text when variables might be missing
2. **Test templates** - Test your templates with different variable values
3. **Keep it simple** - Complex templates may not render well in all notification viewers
4. **Use semantic HTML** - Use proper HTML structure for better rendering
5. **Responsive design** - Consider mobile viewing when designing templates

## Template Loader API

Templates are loaded using the `TemplateLoader` utility:

```python
from admin.utils.template_loader import TemplateLoader

loader = TemplateLoader()
template_content = loader.load_template("new_user_greeting.html")
variables = {
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "app_name": "Telegram User Tracking"
}
content = loader.replace_variables(template_content, variables)
```

## Notes

- Templates are loaded with UTF-8 encoding
- Both HTML and Markdown templates are supported
- Variables are case-sensitive
- Variable names should use snake_case (e.g., `user_name`, not `userName`)

