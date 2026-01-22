#!/usr/bin/env python3
"""
Test description fallback logic for invoices and POs
Part of January 2026 schema transition testing (Phase 5)

Tests the fallback hierarchy:
- Invoice descriptions: Billing → Marketing → Product Name
- PO descriptions: Purchase → Billing → Product Name
- Proposal descriptions: Marketing → Billing → Product Name

Run: streamlit run scripts/features/test_description_fallbacks.py
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_pricing_data
from src.helpers import get_column_value

st.title("🧪 Description Fallback Test")
st.caption("Testing description hierarchy for invoices, POs, and proposals")

# Dataset selector
dataset = st.sidebar.radio("Select Dataset", ["demo", "real"], index=0)

# Load data
try:
    df_template, df_metadata, df_partner_info = load_pricing_data(dataset)
    st.success(f"✅ Loaded {len(df_template)} products from {dataset} dataset")
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

st.divider()

# Test invoice description fallback logic
st.header("📄 Invoice Description Fallback Test")
st.caption("Hierarchy: Billing Description → Marketing Description → Product Name")

invoice_fallback_stats = {
    'Used Billing Description': 0,
    'Used Marketing Description': 0,
    'Used Product Name': 0
}

invoice_examples = {
    'Used Billing Description': [],
    'Used Marketing Description': [],
    'Used Product Name': []
}

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    billing_desc = get_column_value(product, 'billing_description', None)
    marketing_desc = get_column_value(product, 'marketing_description', None)

    # Invoice hierarchy: Billing → Marketing → Name
    if billing_desc and str(billing_desc).strip() and str(billing_desc).strip().lower() != 'nan':
        invoice_fallback_stats['Used Billing Description'] += 1
        if len(invoice_examples['Used Billing Description']) < 3:
            invoice_examples['Used Billing Description'].append({
                'product': product_name,
                'description': billing_desc
            })
    elif marketing_desc and str(marketing_desc).strip() and str(marketing_desc).strip().lower() != 'nan':
        invoice_fallback_stats['Used Marketing Description'] += 1
        if len(invoice_examples['Used Marketing Description']) < 3:
            invoice_examples['Used Marketing Description'].append({
                'product': product_name,
                'description': marketing_desc
            })
    else:
        invoice_fallback_stats['Used Product Name'] += 1
        if len(invoice_examples['Used Product Name']) < 3:
            invoice_examples['Used Product Name'].append({
                'product': product_name,
                'description': product_name
            })

st.write("**Invoice Description Sources:**")
for source, count in invoice_fallback_stats.items():
    pct = (count / len(df_template) * 100) if len(df_template) > 0 else 0
    st.write(f"- {source}: **{count}** products ({pct:.1f}%)")

    # Show examples
    if invoice_examples[source]:
        with st.expander(f"View {len(invoice_examples[source])} example(s)"):
            for ex in invoice_examples[source]:
                st.write(f"**{ex['product']}**")
                st.write(f"Description: {ex['description']}")
                st.write("")

st.divider()

# Test PO description fallback logic
st.header("📋 PO Description Fallback Test")
st.caption("Hierarchy: Purchase Description → Billing Description → Product Name")

po_fallback_stats = {
    'Used Purchase Description': 0,
    'Used Billing Description': 0,
    'Used Product Name': 0
}

po_examples = {
    'Used Purchase Description': [],
    'Used Billing Description': [],
    'Used Product Name': []
}

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    purchase_desc = get_column_value(product, 'purchase_description', None)
    billing_desc = get_column_value(product, 'billing_description', None)

    # PO hierarchy: Purchase → Billing → Name
    if purchase_desc and str(purchase_desc).strip() and str(purchase_desc).strip().lower() != 'nan':
        po_fallback_stats['Used Purchase Description'] += 1
        if len(po_examples['Used Purchase Description']) < 3:
            po_examples['Used Purchase Description'].append({
                'product': product_name,
                'description': purchase_desc
            })
    elif billing_desc and str(billing_desc).strip() and str(billing_desc).strip().lower() != 'nan':
        po_fallback_stats['Used Billing Description'] += 1
        if len(po_examples['Used Billing Description']) < 3:
            po_examples['Used Billing Description'].append({
                'product': product_name,
                'description': billing_desc
            })
    else:
        po_fallback_stats['Used Product Name'] += 1
        if len(po_examples['Used Product Name']) < 3:
            po_examples['Used Product Name'].append({
                'product': product_name,
                'description': product_name
            })

st.write("**PO Description Sources:**")
for source, count in po_fallback_stats.items():
    pct = (count / len(df_template) * 100) if len(df_template) > 0 else 0
    st.write(f"- {source}: **{count}** products ({pct:.1f}%)")

    # Show examples
    if po_examples[source]:
        with st.expander(f"View {len(po_examples[source])} example(s)"):
            for ex in po_examples[source]:
                st.write(f"**{ex['product']}**")
                st.write(f"Description: {ex['description']}")
                st.write("")

st.divider()

# Test proposal/marketing description fallback logic
st.header("📢 Proposal/Marketing Description Fallback Test")
st.caption("Hierarchy: Marketing Description → Billing Description → Product Name")

proposal_fallback_stats = {
    'Used Marketing Description': 0,
    'Used Billing Description': 0,
    'Used Product Name': 0
}

proposal_examples = {
    'Used Marketing Description': [],
    'Used Billing Description': [],
    'Used Product Name': []
}

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    marketing_desc = get_column_value(product, 'marketing_description', None)
    billing_desc = get_column_value(product, 'billing_description', None)

    # Proposal hierarchy: Marketing → Billing → Name
    if marketing_desc and str(marketing_desc).strip() and str(marketing_desc).strip().lower() != 'nan':
        proposal_fallback_stats['Used Marketing Description'] += 1
        if len(proposal_examples['Used Marketing Description']) < 3:
            proposal_examples['Used Marketing Description'].append({
                'product': product_name,
                'description': marketing_desc
            })
    elif billing_desc and str(billing_desc).strip() and str(billing_desc).strip().lower() != 'nan':
        proposal_fallback_stats['Used Billing Description'] += 1
        if len(proposal_examples['Used Billing Description']) < 3:
            proposal_examples['Used Billing Description'].append({
                'product': product_name,
                'description': billing_desc
            })
    else:
        proposal_fallback_stats['Used Product Name'] += 1
        if len(proposal_examples['Used Product Name']) < 3:
            proposal_examples['Used Product Name'].append({
                'product': product_name,
                'description': product_name
            })

st.write("**Proposal Description Sources:**")
for source, count in proposal_fallback_stats.items():
    pct = (count / len(df_template) * 100) if len(df_template) > 0 else 0
    st.write(f"- {source}: **{count}** products ({pct:.1f}%)")

    # Show examples
    if proposal_examples[source]:
        with st.expander(f"View {len(proposal_examples[source])} example(s)"):
            for ex in proposal_examples[source]:
                st.write(f"**{ex['product']}**")
                st.write(f"Description: {ex['description']}")
                st.write("")

st.divider()

# Show products with missing descriptions
st.header("⚠️ Products with Missing Descriptions")

missing_all = []
missing_purchase = []
missing_billing = []
missing_marketing = []

for idx, product in df_template.iterrows():
    product_name = get_column_value(product, 'product_service_name', 'Unknown')
    purchase_desc = get_column_value(product, 'purchase_description', None)
    billing_desc = get_column_value(product, 'billing_description', None)
    marketing_desc = get_column_value(product, 'marketing_description', None)

    # Check for non-empty, non-NaN values
    has_purchase = purchase_desc and str(purchase_desc).strip() and str(purchase_desc).strip().lower() != 'nan'
    has_billing = billing_desc and str(billing_desc).strip() and str(billing_desc).strip().lower() != 'nan'
    has_marketing = marketing_desc and str(marketing_desc).strip() and str(marketing_desc).strip().lower() != 'nan'

    if not has_purchase and not has_billing and not has_marketing:
        missing_all.append(product_name)
    else:
        if not has_purchase:
            missing_purchase.append(product_name)
        if not has_billing:
            missing_billing.append(product_name)
        if not has_marketing:
            missing_marketing.append(product_name)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if missing_all:
        st.error(f"**All 3 missing:** {len(missing_all)}")
        with st.expander("View"):
            for name in missing_all:
                st.write(f"- {name}")
    else:
        st.success("**All 3 missing:** 0")

with col2:
    if missing_purchase:
        st.warning(f"**Purchase missing:** {len(missing_purchase)}")
        with st.expander("View"):
            for name in missing_purchase[:10]:
                st.write(f"- {name}")
            if len(missing_purchase) > 10:
                st.write(f"... and {len(missing_purchase) - 10} more")
    else:
        st.success("**Purchase missing:** 0")

with col3:
    if missing_billing:
        st.warning(f"**Billing missing:** {len(missing_billing)}")
        with st.expander("View"):
            for name in missing_billing[:10]:
                st.write(f"- {name}")
            if len(missing_billing) > 10:
                st.write(f"... and {len(missing_billing) - 10} more")
    else:
        st.success("**Billing missing:** 0")

with col4:
    if missing_marketing:
        st.warning(f"**Marketing missing:** {len(missing_marketing)}")
        with st.expander("View"):
            for name in missing_marketing[:10]:
                st.write(f"- {name}")
            if len(missing_marketing) > 10:
                st.write(f"... and {len(missing_marketing) - 10} more")
    else:
        st.success("**Marketing missing:** 0")

st.divider()

# Summary
st.header("✅ Test Summary")

if missing_all:
    st.error(f"⚠️ {len(missing_all)} products missing ALL descriptions (will use product name)")
else:
    st.success("✓ All products have at least one description field")

# Check if fallbacks are working as expected
invoice_primary_usage = invoice_fallback_stats['Used Billing Description']
po_primary_usage = po_fallback_stats['Used Purchase Description']
proposal_primary_usage = proposal_fallback_stats['Used Marketing Description']

total = len(df_template)
invoice_pct = (invoice_primary_usage / total * 100) if total > 0 else 0
po_pct = (po_primary_usage / total * 100) if total > 0 else 0
proposal_pct = (proposal_primary_usage / total * 100) if total > 0 else 0

st.write("**Primary Description Field Usage:**")
st.write(f"- Invoices using Billing Description (primary): {invoice_primary_usage}/{total} ({invoice_pct:.1f}%)")
st.write(f"- POs using Purchase Description (primary): {po_primary_usage}/{total} ({po_pct:.1f}%)")
st.write(f"- Proposals using Marketing Description (primary): {proposal_primary_usage}/{total} ({proposal_pct:.1f}%)")

st.success("🎉 Description fallback test complete!")

st.caption("Phase 5: Testing & Validation - January 2026 Schema Transition")
