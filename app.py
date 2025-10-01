"""
Peace by Piece International - Pricing & Quoting App
Simple MVP for product selection, quote calculation, and proposal/invoice generation.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="PBP Pricing App",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Peace by Piece Pricing & Quoting App")

# ===== GOOGLE SHEETS CONNECTION =====
@st.cache_resource
def connect_to_sheets():
    """
    Connect to Google Sheets using service account credentials.
    Cached so we don't reconnect on every rerun.
    """
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_pricing_data():
    """
    Load pricing data from master_pricing_demo Google Sheet.
    Returns a pandas DataFrame.
    """
    gc = connect_to_sheets()
    sheet = gc.open("master_pricing_demo").sheet1
    data = pd.DataFrame(sheet.get_all_records())
    return data

# Load data
try:
    df = load_pricing_data()
    st.success(f"✅ Loaded {len(df)} products from master_pricing_demo")
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ===== PRODUCT SELECTION =====
st.header("1️⃣ Select Products")

# Create dropdowns for filtering
col1, col2 = st.columns(2)

with col1:
    # Partner dropdown
    partners = ["All Partners"] + sorted(df["Partner"].unique().tolist())
    selected_partner = st.selectbox("Select Partner", partners)

with col2:
    # Filter products based on partner selection
    if selected_partner == "All Partners":
        available_products = df["Product"].unique().tolist()
    else:
        available_products = df[df["Partner"] == selected_partner]["Product"].unique().tolist()

    selected_product = st.selectbox("Select Product", available_products)

# Get selected product details
if selected_partner == "All Partners":
    product_data = df[df["Product"] == selected_product].iloc[0]
else:
    product_data = df[(df["Partner"] == selected_partner) & (df["Product"] == selected_product)].iloc[0]

# Display product details
st.subheader("📦 Product Details")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Partner", product_data["Partner"])
with col2:
    st.metric("Base Price", f"${product_data['Price']:.2f}")
with col3:
    st.metric("Currency", product_data["Currency"])

st.info(f"**Notes:** {product_data['Notes']}")

# ===== QUOTE CUSTOMIZATION =====
st.header("2️⃣ Customize Quote")

col1, col2, col3, col4 = st.columns(4)

with col1:
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)

with col2:
    # Default markup is 100% (meaning 2x the base price)
    markup_percent = st.number_input("Markup %", min_value=0.0, value=100.0, step=5.0)

with col3:
    shipping = st.number_input("Shipping Cost ($)", min_value=0.0, value=0.0, step=10.0)

with col4:
    tariff = st.number_input("Tariff Cost ($)", min_value=0.0, value=0.0, step=10.0)

# ===== QUOTE CALCULATION =====
st.header("3️⃣ Quote Calculation")

# Calculate quote
# Formula: (base_price * markup_percentage) + shipping + tariff
base_price = product_data["Price"]
markup_multiplier = 1 + (markup_percent / 100)
unit_price_with_markup = base_price * markup_multiplier
total_per_unit = unit_price_with_markup + (shipping / quantity) + (tariff / quantity)
total_quote = total_per_unit * quantity

# Display calculation breakdown
st.subheader("💵 Price Breakdown (Per Unit)")
breakdown_df = pd.DataFrame({
    "Item": [
        "Base Price",
        f"Markup ({markup_percent}%)",
        "Price After Markup",
        "Shipping (per unit)",
        "Tariff (per unit)",
        "Total Per Unit"
    ],
    "Amount": [
        f"${base_price:.2f}",
        f"${base_price * (markup_percent / 100):.2f}",
        f"${unit_price_with_markup:.2f}",
        f"${shipping / quantity:.2f}",
        f"${tariff / quantity:.2f}",
        f"${total_per_unit:.2f}"
    ]
})
st.table(breakdown_df)

# Display total
st.success(f"### 💰 Total Quote: ${total_quote:.2f} ({quantity} units @ ${total_per_unit:.2f} each)")

# ===== PROPOSAL GENERATION =====
st.header("4️⃣ Proposal")

st.subheader("📄 Quote Proposal")
proposal_df = pd.DataFrame({
    "Item": ["Product Name", "Partner", "Quantity", "Unit Price", "Subtotal", "Shipping", "Tariff", "Total"],
    "Details": [
        product_data["Product"],
        product_data["Partner"],
        quantity,
        f"${total_per_unit:.2f}",
        f"${unit_price_with_markup * quantity:.2f}",
        f"${shipping:.2f}",
        f"${tariff:.2f}",
        f"${total_quote:.2f}"
    ]
})
st.table(proposal_df)

st.info("💡 Copy this table and paste into your proposal template.")

# ===== INVOICE GENERATION =====
st.header("5️⃣ Invoice")

st.subheader("🧾 Invoice")
invoice_date = datetime.now().strftime("%Y-%m-%d")
invoice_df = pd.DataFrame({
    "Field": ["Invoice Date", "Product", "Partner", "Quantity", "Unit Price", "Total Amount Due"],
    "Value": [
        invoice_date,
        product_data["Product"],
        product_data["Partner"],
        quantity,
        f"${total_per_unit:.2f}",
        f"${total_quote:.2f}"
    ]
})
st.table(invoice_df)

st.info("💡 Copy this table and paste into your invoice template.")

# ===== FOOTER =====
st.divider()
st.caption(f"Last data refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💡 Click menu → 'Rerun' to refresh pricing data from Google Sheets")
