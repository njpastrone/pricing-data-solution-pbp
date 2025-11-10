"""
Simple Python test to verify both datasets are accessible
"""

import sys
sys.path.insert(0, '/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp')

# Mock streamlit for testing
class MockStreamlit:
    class secrets:
        gcp_service_account = {
            "type": "service_account",
            "project_id": "pricing-data-solutions-pbp",
            "private_key_id": "5c0ced56ee64d9ef17e6779705b8070d2e8eb6f4",
            "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC0LvVD+z+F7vnC
j2Syu5krHCkqzhPVUlmAYsUfIDxMHNVY6pPO+nvaKoWbDeBXuPgSG8nn54AvUnR0
khVDieVm/jEzTVuIxft+guVRPxAtcIbv0mdHE+TPNODrsROT5UOrEfOUhEd4vjkp
gE43msMVJyAAIBWI8HUMRhh2f7RIKSYjrvGj6ZolCNzLOHAqhvi4DDymgy3FXGB1
ZDccVN9mGyNsu4rWhTi6R3qqTf/atpUwoUyW63ASO6xAcEcMEliIUFJTsEoIGrQY
pD4c90K24HGtS2TwMwxOYhRKNjMO/44OHcFioCpjJvkEuAUuTRtEtVP8n1nPsTNv
axx/Hg6xAgMBAAECggEAGNF7AQEjb8xJ5K2hnijO4SxA01+NRc3Q/Ckeo7np9EXo
cRXmhBTmaFeBDalspEibCst/FQ1DD8GYvtG8UhA1Y+lRV5KpL/6tNHDNK1K3ZLri
Kzhc92JbGttau7wpSS7EElUnquZJfe0drIS6wVf01P4Nn1bMAI+2X5lsFy5h46pk
JKqt8dVV+idL3cbgmCBP+scAQTclAJwx23Z0i9TlG1oHxmDp18yyn4tsQf2KUC4S
Re58dxdGTnHFm9KnRwraH7aCOfD8NoAcmX0Mto3TMk4r/GPyr3DyeTcUmGV/+vSv
qmUWaWdmKxJIhdmD9Q3OSjvXm7U4C81xceacffl10QKBgQDalwfn3YHEUtA0Lzaw
Ryi+7F5W4QjXWFk/NkGP76L4Vzhn+nEfKbsQiW2xxjZNsLKdRJLa11zEuHTKUlzQ
fOPrlqDaZ9YWQbf2QAdyw1mnR1D9CIsHbuoDMaiYPeAvA7kuiIAgbl8WHSqcJKXU
eF7SpGSKbqWHxxD81C1n7qrRJQKBgQDTBT3WAS/GLmjs+1R2m4IRqiF2B4P5PnDI
Q7/Df1mX3y5rdiDIY85B0iEOszTtBIq4JEzEV720zWVTJu3bEtJlC03p+EvONM7Q
+MDrH7DJAW41z8ZDCOHA0c/PCuMQiaAVpLujb5DsRfkVqUBWIP5+2STc9xSghIOX
eOVwmT4vnQKBgCsfeobKkywo7jwtSEu0bhxkQyQ+luDs5AZtbLe5ndwCUPVqWeC8
+dOEWSimItZm0oXmHlagAAQrI5c6cmcLDGfQuoD71Sdk5abl8NI6KbivgBG7Grpn
rjDdHhaStmRwBptggG5ld8rEDEDrle95o7NIjTEmLO/BXN+T+DU1x2slAoGARIgb
QPk5rr87zFsDX1G5uErsewyNy9B/iEqYaMFfM3eD99pxYyMmxTGdEs0YjzE+a/c+
BzYHokRid9LYxKEkOzSkpSvCUsHLuQpQfQvZui4AwPEtjm/AAYMiXjdG7wQDPYQ2
fCmrg1BmSKajAlXM0R1sX2bPCCKBKhxVR3A9RfECgYEAygJVCHjXmgbqGG1Kkcf0
BQ/tYaVLknYS7Fxi7rRFo8sOvCCtzKOR9wpHmDgCSTgJUNJglpfPlhFkE3YqEDCE
QAf9335Wc0VQBn7P8UAmQaQJYNMACCEO/LhfVlPV4gIgi2rCBarwXRG+q8GSW4EY
r7BjeDWAAbWe8Z93O/GRH8g=
-----END PRIVATE KEY-----
""",
            "client_email": "pbp-app-service@pricing-data-solutions-pbp.iam.gserviceaccount.com",
            "client_id": "109370231920177008678",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/pbp-app-service%40pricing-data-solutions-pbp.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

    @staticmethod
    def cache_resource(func):
        return func

    @staticmethod
    def cache_data(ttl=None, show_spinner=None):
        def decorator(func):
            return func
        return decorator

sys.modules['streamlit'] = MockStreamlit()

import gspread
from google.oauth2.service_account import Credentials

# Test both datasets
DATASETS = {
    'demo': 'https://docs.google.com/spreadsheets/d/1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs',
    'real': 'https://docs.google.com/spreadsheets/d/1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms'
}

print("Testing dataset connections...\n")

creds_info = MockStreamlit.secrets.gcp_service_account
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

for dataset_name, url in DATASETS.items():
    print(f"Testing {dataset_name} dataset...")
    try:
        spreadsheet = gc.open_by_url(url)
        template_sheet = spreadsheet.worksheet("Template")
        template_values = template_sheet.get_all_values()

        # Count rows (excluding headers)
        num_rows = len(template_values) - 6  # Header at row 6

        print(f"  ✓ {dataset_name.upper()}: Connected successfully")
        print(f"  ✓ Template sheet has {num_rows} data rows")
        print()

    except Exception as e:
        print(f"  ✗ {dataset_name.upper()}: Failed - {str(e)}")
        print()

print("Test complete!")
