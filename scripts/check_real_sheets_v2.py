"""
Check what sheets exist in the real pricing dataset
Using actual secrets from .streamlit/secrets.toml
"""

import gspread
from google.oauth2.service_account import Credentials
import toml

# Load secrets
secrets = toml.load('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp/.streamlit/secrets.toml')

real_url = 'https://docs.google.com/spreadsheets/d/1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms'

print("Checking sheets in real pricing dataset...\n")

creds_info = secrets['gcp_service_account']
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

try:
    spreadsheet = gc.open_by_url(real_url)
    worksheets = spreadsheet.worksheets()

    print(f"Spreadsheet title: {spreadsheet.title}")
    print(f"Total sheets found: {len(worksheets)}\n")

    print("Available sheets:")
    for idx, sheet in enumerate(worksheets, 1):
        print(f"  {idx}. '{sheet.title}' ({sheet.row_count} rows × {sheet.col_count} cols)")

except Exception as e:
    print(f"Error: {str(e)}")
