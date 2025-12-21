# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /config
Purpose: Application configuration files

---

## Quick Context
- **Primary responsibility**: Static configuration data for the application
- **Key dependencies**: None (configuration only)
- **Used by**: app.py for terms & conditions display
- **Technology stack**: Plain text

---

## Detailed Overview

The `config/` directory contains static configuration files used by the application. Currently, it holds only terms and conditions text that appears in the client order form generator (Tab 2).

This directory is designed for:
1. **Static text content** - Terms, conditions, disclaimers
2. **Configuration data** - App settings that rarely change
3. **Reference text** - Legal or compliance-related content

**Note:** Most app configuration happens via:
- `st.session_state` for runtime state
- `.streamlit/secrets.toml` for credentials
- Environment variables for deployment

---

## Important Files

### terms_conditions.txt (837 bytes)
**Purpose:** Terms and conditions text for client order forms

**Contents:**
- Legal disclaimer
- Order terms
- Payment conditions
- Shipping policies

**Usage:**
```python
# In app.py (Tab 2)
with open('config/terms_conditions.txt', 'r') as f:
    terms_text = f.read()

# Display in HTML order form
html_content += f"<p>{terms_text}</p>"
```

**When modified:**
- Legal review of terms
- Policy changes
- Compliance updates

**Notes:**
- Plain text format
- No special formatting needed
- Embedded in HTML order forms
- Not actively used in current version (feature deprecated/changed)

---

## Code Patterns & Conventions

### Loading Configuration
```python
import os

# Check if file exists
config_path = 'config/terms_conditions.txt'
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        content = f.read()
else:
    # Fallback to default
    content = "Default terms and conditions"
```

### Adding New Config Files
1. Create file in `config/` directory
2. Use descriptive name (e.g., `privacy_policy.txt`, `shipping_policy.txt`)
3. Load in app.py where needed
4. Document in this README

---

## Common Tasks

### To update terms and conditions:
1. Edit `config/terms_conditions.txt`
2. Test in Tab 2 (Client Order Form Generator)
3. Verify HTML export includes updated text
4. Commit changes with clear message

### To add new configuration:
1. Create new file: `config/new_setting.txt`
2. Load in app.py:
   ```python
   with open('config/new_setting.txt', 'r') as f:
       setting = f.read()
   ```
3. Update this documentation
4. Test thoroughly

---

## Important Notes

### Current Usage
The `terms_conditions.txt` file is **not actively used** in current version:
- Tab 2 order forms have customizable template text
- Terms may be included via template customization
- File kept for backward compatibility

### Future Configuration
Potential uses for config/ directory:
- **Email templates** - Pre-formatted email text
- **Default values** - App-wide defaults
- **Legal text** - Privacy policy, disclaimers
- **Partner configs** - Partner-specific settings (if not in Google Sheets)

### Not for Credentials
**Never store credentials or secrets in config/**
- Use `.streamlit/secrets.toml` for local credentials
- Use environment variables for production credentials
- config/ is for non-sensitive configuration only

### Version Control
- Config files ARE checked into git
- Safe to commit (no sensitive data)
- Track changes in commit history

---

## Performance Considerations

### File Size
- All config files are small (<1KB each)
- Loaded once at startup or on-demand
- Minimal performance impact

### Caching
Not currently cached, but could be:
```python
@st.cache_data
def load_config(filename):
    with open(f'config/{filename}', 'r') as f:
        return f.read()
```

---

## Gotchas & Notes

### Line Endings
- Use Unix line endings (LF) not Windows (CRLF)
- Git should handle automatically
- If issues, check `.gitattributes`

### Encoding
- Use UTF-8 encoding for all text files
- Avoid special characters unless necessary
- Test with non-ASCII characters if used

### File Paths
- Always use relative paths from project root
- `config/terms_conditions.txt` not `./config/...`
- Works correctly in both local and production (Render)

---

## Future Enhancements

### Structured Configuration
Could use JSON/YAML for complex config:
```json
{
  "app_settings": {
    "default_markup": 100,
    "default_discount": 5,
    "marketing_rounding": true
  },
  "text_content": {
    "terms": "config/terms_conditions.txt",
    "privacy": "config/privacy_policy.txt"
  }
}
```

### Environment-Specific Config
Different configs for dev/production:
```
config/
├── terms_conditions.txt (shared)
├── dev.json (development settings)
└── production.json (production settings)
```

### Database-Driven Config
Move to Google Sheets for easier updates:
- Add "App Settings" sheet
- Load settings at startup
- Non-technical users can update

---

## Links & Resources

- **Main README:** [../README.md](../README.md)
- **App Code:** [../app.py](../app.py)
- **Tab 2 Documentation:** (See app.py Tab 2 section)

---

## Summary

The `config/` directory currently contains a single terms & conditions file that is not actively used in the current version. It serves as a placeholder for future static configuration needs.

**Current state:** Minimal usage
**Future potential:** Email templates, default settings, legal text
**Not for:** Credentials, secrets, or dynamic data
