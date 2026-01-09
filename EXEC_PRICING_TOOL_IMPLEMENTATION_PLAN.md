# Executive Pricing Tool Tab - Implementation Plan

## Codebase Findings

### 1. Tab Structure
- Tabs are defined at line 2218 in `app.py` using `st.tabs()`
- Each tab has its own section with `with tab1:`, `with tab2:`, etc.
- Current 4-tab structure: Proposal Generator, Client Order Form Generator, Order & Client Info, Execution & Accounting

### 2. Key Existing Functions to Reuse
**Data Loading:**
- `load_pricing_data()` - loads from selected dataset (demo/real)
- Dataset selector at line 640 stores in `st.session_state.selected_dataset`
- Data cached in `st.session_state.df_template`, `df_metadata`, `df_partner_info`

**Pricing Calculations:**
- `get_unit_price_new_system()` - gets base cost with package normalization
- `clean_price()` - converts price strings to floats
- `get_column_value()` - handles new/old column name compatibility
- `get_default_markup()` - gets PBP Standard Markup from spreadsheet
- `calculate_markup_from_price()` - back-calculates markup from price

**Additional Costs:**
- `get_shipping_costs()` - extracts shipping costs
- `get_tariff_rate()` - gets tariff rate (% or $)
- `calculate_product_tariff()` - calculates tariff amount

**CSV Export:**
- Pattern: `df.to_csv(index=False)` then `st.download_button()`

### 3. Proposal/Order Structure
**Proposal items contain:**
```python
{
    'product_data': product_row.to_dict(),  # Full row from spreadsheet
    'markup_percent': float  # Markup percentage
}
```

**Order items extend proposals with:**
- `quantity`, `has_customization`, `customization_setup_fee`, `customization_per_unit`, etc.

### 4. Bidirectional Editing Pattern
Current implementation uses flags to prevent circular updates:
1. User edits markup → price recalculates → set flag `updating_from_markup_X`
2. User edits price → markup back-calculates → set flag `updating_from_price_X`
3. Flags prevent infinite loops between the two input fields

### 5. Import Pattern
- Proposals stored in `st.session_state.proposal_products`
- Orders stored in `st.session_state.order_items`
- Import typically appends items and shows success toast

## Implementation Approach

### File Structure
- **Add code inline in `app.py`** (consistent with current tabs)
- Position as Tab 5 after current tabs
- Use existing helper functions from `src/` modules

### Key Design Decisions
1. **Respect dataset selector** - Use `st.session_state.selected_dataset`
2. **Reuse existing pricing engine** - Don't duplicate calculations
3. **Follow bidirectional editing pattern** - Use flags to prevent loops
4. **Use st.data_editor** - For editable table with multiple price columns
5. **Progressive disclosure** - Start simple, expand with filters/options

## Detailed Implementation Steps

### Step 1: Add Tab 5 Definition
```python
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Proposal Generator",
    "Client Order Form Generator", 
    "Order & Client Info",
    "Execution & Accounting",
    "Executive Pricing Tool"
])
```

### Step 2: Create Tab 5 Section Structure
```python
with tab5:
    st.header("Executive Pricing Tool")
    st.caption("Experiment with pricing scenarios and import to proposals/orders")
    
    # Check data is loaded
    if 'df_template' not in st.session_state:
        st.error("Please load data first")
        st.stop()
```

### Step 3: Global Markup Control
```python
# Global markup slider and input
col1, col2 = st.columns([3, 1])
with col1:
    global_markup = st.slider("Global Markup %", 0, 200, 100, 5)
with col2:
    global_markup = st.number_input("", value=global_markup, min_value=0, max_value=200)
```

### Step 4: Partner Filter
```python
# Partner filter
all_partners = df_template['Partner'].unique().tolist()
selected_partner = st.selectbox(
    "Filter by Partner", 
    ["All Partners"] + all_partners
)
```

### Step 5: Build Pricing Table Data
```python
# Build table data
pricing_data = []
for _, row in filtered_df.iterrows():
    # Get base cost
    base_cost, _, _ = get_unit_price_new_system(row, 100)
    if not base_cost:
        continue
    
    # Get additional costs
    customization_setup = clean_price(get_column_value(row, 
        'PBP Cost: Customization Setup Fee',
        'Customization Setup Fee', 0))
    customization_per_unit = clean_price(get_column_value(row,
        'PBP Cost: Customization Cost per Unit',
        'Customization Cost per Unit', 0))
    shipping = clean_price(get_column_value(row,
        'PBP Cost: Shipping Cost per Unit',
        'Shipping Cost per Unit', 0))
    tariff = calculate_product_tariff(row, 100)
    
    # Calculate prices with markup
    markup = global_markup  # Start with global
    client_base = base_cost * (1 + markup/100)
    with_custom = client_base + (customization_setup/100) + customization_per_unit
    with_shipping = with_custom + shipping
    fully_loaded = with_shipping + tariff
    
    # Get MSRP for comparison
    msrp = clean_price(get_column_value(row, 'Vendor Published MSRP', 'MSRP', 0))
    
    pricing_data.append({
        'Partner': row['Partner'],
        'Product': row['Product/Service'],
        'PBP Cost': base_cost,
        'Markup %': markup,
        'Client Price (Base)': client_base,
        '+ Customization': with_custom,
        '+ Shipping': with_shipping,
        'Fully Loaded': fully_loaded,
        'MSRP': msrp if msrp else None,
        'vs MSRP %': ((fully_loaded - msrp)/msrp * 100) if msrp else None,
        'row_data': row.to_dict()  # Store full data for import
    })
```

### Step 6: Editable Data Editor
```python
# Create editable dataframe
df_pricing = pd.DataFrame(pricing_data)

# Configure column settings for st.data_editor
column_config = {
    'Partner': st.column_config.TextColumn('Partner', disabled=True),
    'Product': st.column_config.TextColumn('Product', disabled=True),
    'PBP Cost': st.column_config.NumberColumn('PBP Cost', disabled=True, format="$%.2f"),
    'Markup %': st.column_config.NumberColumn('Markup %', min_value=0, max_value=500),
    'Client Price (Base)': st.column_config.NumberColumn('Base Price', format="$%.2f"),
    '+ Customization': st.column_config.NumberColumn('w/ Custom', format="$%.2f"),
    '+ Shipping': st.column_config.NumberColumn('w/ Shipping', format="$%.2f"),
    'Fully Loaded': st.column_config.NumberColumn('Fully Loaded', format="$%.2f"),
    'MSRP': st.column_config.NumberColumn('MSRP', disabled=True, format="$%.2f"),
    'vs MSRP %': st.column_config.NumberColumn('vs MSRP', disabled=True, format="%.1f%%"),
    'row_data': None  # Hide this column
}

# Editable table
edited_df = st.data_editor(
    df_pricing,
    column_config=column_config,
    hide_index=True,
    use_container_width=True,
    key="pricing_editor"
)
```

### Step 7: Handle Bidirectional Editing
```python
# After user edits, recalculate dependent columns
# This happens automatically with st.data_editor callbacks
# We'll need to detect which column changed and update others accordingly

def on_markup_change(row_idx):
    # Recalculate all price columns based on new markup
    pass

def on_price_change(row_idx, price_column):
    # Back-calculate markup from price
    # Then recalculate other price columns
    pass
```

### Step 8: Import to Proposal/Order
```python
st.divider()
st.subheader("Import to Proposal/Order")

# Product selection
selected_indices = st.multiselect(
    "Select products to import",
    options=range(len(edited_df)),
    format_func=lambda x: edited_df.iloc[x]['Product']
)

col1, col2 = st.columns(2)
with col1:
    if st.button("Import to Current Proposal", type="primary", disabled=len(selected_indices)==0):
        for idx in selected_indices:
            row = edited_df.iloc[idx]
            proposal_item = {
                'product_data': row['row_data'],
                'markup_percent': row['Markup %']
            }
            st.session_state.proposal_products.append(proposal_item)
        st.toast(f"Added {len(selected_indices)} products to proposal")
        st.rerun()

with col2:
    if st.button("Import to Current Order", disabled=len(selected_indices)==0):
        for idx in selected_indices:
            row = edited_df.iloc[idx]
            order_item = convert_proposal_to_order(
                {'product_data': row['row_data'], 'markup_percent': row['Markup %']},
                get_unit_price_new_system,
                calculate_product_tariff
            )
            st.session_state.order_items.append(order_item)
        st.toast(f"Added {len(selected_indices)} products to order")
        st.rerun()
```

### Step 9: CSV Export
```python
# Export button
csv = edited_df[display_columns].to_csv(index=False)
st.download_button(
    label="Download Pricing Analysis (CSV)",
    data=csv,
    file_name=f"pricing_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
```

## Edge Cases to Handle

1. **Missing data**: Use 0 defaults for missing costs (customization, shipping, tariff)
2. **Units per Package**: Already handled by `get_unit_price_new_system()`
3. **Tiered pricing**: Use quantity 100 as reference (consistent with MOQ calculations)
4. **Negative markup**: Allow but show warning (below cost)
5. **Price below add-ons**: When fully loaded < sum of add-ons, show error
6. **Duplicate imports**: Check if product already in proposal/order before adding
7. **Dataset switching**: Clear/warn when dataset changes mid-session

## UX Considerations

1. **Start simple**: Show base table, hide complexity in expanders
2. **Visual feedback**: Color code vs MSRP (green=good, red=over, gray=no MSRP)
3. **Inline help**: Tooltips explaining each column
4. **Responsive editing**: Real-time updates as user types
5. **Clear CTAs**: Import buttons prominent when products selected
6. **Success feedback**: Toast notifications for imports

## Estimated Scope
- **Lines of code**: ~400-500 lines
- **Files to modify**: Only `app.py`
- **New functions**: 2-3 helper functions for bidirectional editing
- **Complexity**: Medium (mostly reusing existing patterns)

## Open Questions
1. Should we allow quantity input per product, or assume quantity 100 for all?
2. Should the global markup override individual markups, or just set initial values?
3. Should we show all products by default, or require partner selection first?
4. How should we handle the bidirectional editing with st.data_editor (may need callbacks)?