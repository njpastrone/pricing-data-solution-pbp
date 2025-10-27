"""
Check jaggery_demo sheet structure (non-Streamlit)
"""
import gspread
from google.oauth2.service_account import Credentials
import json

# Load credentials from secrets.toml
with open('.streamlit/secrets.toml', 'r') as f:
    content = f.read()
    # Extract JSON from TOML
    start = content.find('{')
    end = content.rfind('}') + 1
    creds_json = content[start:end]
    creds_info = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

print("Connecting to jaggery_demo...")
sheet = gc.open("jaggery_demo").sheet1

# Get all values
all_values = sheet.get_all_values()

print(f"\n✅ Connected successfully!")
print(f"Sheet title: {sheet.title}")
print(f"Row count: {len(all_values)}")
print(f"Column count: {len(all_values[0]) if all_values else 0}")

print("\n" + "="*80)
print("FIRST 5 ROWS (Raw)")
print("="*80)
for i, row in enumerate(all_values[:5], 1):
    print(f"Row {i}: {row[:8]}...")  # First 8 columns

print("\n" + "="*80)
print("HEADERS (Row 2, index 1)")
print("="*80)
headers = [col.strip() for col in all_values[1]]
for i, h in enumerate(headers, 1):
    print(f"{i}. '{h}'")

print("\n" + "="*80)
print("FIRST PRODUCT (Row 3, index 2)")
print("="*80)
first_product = all_values[2]
product_dict = dict(zip(headers, first_product))

print(f"Product Ref: {product_dict.get('Product Ref. No.', 'N/A')}")
print(f"Gift Name: {product_dict.get('Gift Name', 'N/A')}")
print(f"Partner: {product_dict.get('Artisan Partner', 'N/A')}")

print("\nPricing Tiers:")
pricing_cols = [
    'PBP Cost w/o shipping (1-25)',
    'PBP Cost w/o shipping (26-50)',
    'PBP Cost w/o shipping (51-100)',
    'PBP Cost w/o shipping (101-250)',
    'PBP Cost w/o shipping (251-500)',
    'PBP Cost w/o shipping (501-1000)',
    'PBP Cost w/o shipping (1000+)'
]

for col in pricing_cols:
    value = product_dict.get(col, 'COLUMN NOT FOUND')
    empty = "(EMPTY)" if value == '' else ""
    print(f"  {col}: '{value}' {empty}")

print("\nAdditional Costs:")
print(f"  Art Setup Fee: {product_dict.get('Art Setup Fee', 'N/A')}")
labels_col = 'Labels up to 1" x 2.5\''
print(f"  Labels: {product_dict.get(labels_col, 'N/A')}")
print(f"  Minimum for labels: {product_dict.get('Minimum for labels', 'N/A')}")

print("\n" + "="*80)
print("KEY DIFFERENCES FROM jaggery_sample_6_23")
print("="*80)
print("1. Header row location: Row 2 (index 1) vs Row 5 (index 4)")
print("2. Data starts: Row 3 (index 2) vs Row 6 (index 5)")
print("3. Empty rows at top: 1 row vs 5 rows")

print("\n✅ Investigation complete!")
