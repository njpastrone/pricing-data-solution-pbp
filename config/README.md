# Configuration Files

Static configuration and text content for the application.

**Last Updated:** 2024-12-20
**Files:** 1

---

## Overview

This directory contains configuration files for the application. Currently minimal, with only terms and conditions text.

---

## Files

### terms_conditions.txt (837 bytes)
**Purpose:** Terms and conditions for client order forms

**Usage:**
- Loaded in Tab 2 (Client Order Form Generator)
- Embedded in HTML order forms
- **Note:** Not actively used in current version (template customization replaced it)

**To update:**
1. Edit the file
2. Test in Tab 2
3. Commit changes

---

## Usage

### Loading Configuration
```python
with open('config/terms_conditions.txt', 'r') as f:
    terms = f.read()
```

---

## Notes

- **Not for credentials** - Use `.streamlit/secrets.toml` or environment variables
- **Safe to commit** - No sensitive data
- **UTF-8 encoding** - Use for all text files

---

## Future Uses

Potential future configuration:
- Email templates
- Default app settings
- Legal/compliance text
- Partner-specific configs

---

## Links

- **CLAUDE.md:** [CLAUDE.md](CLAUDE.md) - AI context
- **Main README:** [../README.md](../README.md)
