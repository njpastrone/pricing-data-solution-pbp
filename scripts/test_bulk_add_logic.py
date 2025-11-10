"""
Test bulk add logic to verify duplicate detection and counting works correctly
"""

import pandas as pd

# Simulate filtered products
filtered_products = pd.DataFrame({
    'Product/Service': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
    'Partner': ['Partner X', 'Partner X', 'Partner Y', 'Partner X', 'Partner Y'],
    'PBP Cost (No Tiers)': [10, 15, 20, 25, 30]
})

# Simulate existing proposal (Product B and Product D already added)
existing_proposal = [
    {'product_data': {'Product/Service': 'Product B', 'Partner': 'Partner X'}, 'markup_percent': 100.0},
    {'product_data': {'Product/Service': 'Product D', 'Partner': 'Partner X'}, 'markup_percent': 100.0}
]

print("Test Case 1: Add all from Partner X")
print("=" * 60)

# Select Partner X
bulk_partners = ['Partner X']
products_to_add = filtered_products[filtered_products["Partner"].isin(bulk_partners)]
print(f"Total products from Partner X: {len(products_to_add)}")
print(f"Products: {products_to_add['Product/Service'].tolist()}")

# Get existing product names
existing_products = {item['product_data']['Product/Service'] for item in existing_proposal}
print(f"\nExisting products in proposal: {existing_products}")

# Filter out duplicates
new_products = []
for idx, row in products_to_add.iterrows():
    if row['Product/Service'] not in existing_products:
        new_products.append(row)

new_count = len(new_products)
duplicate_count = len(products_to_add) - new_count

print(f"\nNew products to add: {new_count}")
print(f"New product names: {[p['Product/Service'] for p in new_products]}")
print(f"Duplicates (will skip): {duplicate_count}")

assert new_count == 1, "Should add 1 new product (A from Partner X, skip B and D)"
assert duplicate_count == 2, "Should have 2 duplicates (B and D)"

print("\n✅ Test Case 1 PASSED")

print("\n" + "=" * 60)
print("Test Case 2: Add all from Partner Y")
print("=" * 60)

bulk_partners = ['Partner Y']
products_to_add = filtered_products[filtered_products["Partner"].isin(bulk_partners)]
print(f"Total products from Partner Y: {len(products_to_add)}")
print(f"Products: {products_to_add['Product/Service'].tolist()}")

# Filter out duplicates
new_products = []
for idx, row in products_to_add.iterrows():
    if row['Product/Service'] not in existing_products:
        new_products.append(row)

new_count = len(new_products)
duplicate_count = len(products_to_add) - new_count

print(f"\nNew products to add: {new_count}")
print(f"New product names: {[p['Product/Service'] for p in new_products]}")
print(f"Duplicates (will skip): {duplicate_count}")

assert new_count == 2, "Should add 2 new products (C and E from Partner Y)"
assert duplicate_count == 0, "Should have 0 duplicates"

print("\n✅ Test Case 2 PASSED")

print("\n" + "=" * 60)
print("Test Case 3: Add from multiple partners")
print("=" * 60)

bulk_partners = ['Partner X', 'Partner Y']
products_to_add = filtered_products[filtered_products["Partner"].isin(bulk_partners)]
print(f"Total products from both partners: {len(products_to_add)}")
print(f"Products: {products_to_add['Product/Service'].tolist()}")

# Filter out duplicates
new_products = []
for idx, row in products_to_add.iterrows():
    if row['Product/Service'] not in existing_products:
        new_products.append(row)

new_count = len(new_products)
duplicate_count = len(products_to_add) - new_count

print(f"\nNew products to add: {new_count}")
print(f"New product names: {[p['Product/Service'] for p in new_products]}")
print(f"Duplicates (will skip): {duplicate_count}")

assert new_count == 3, "Should add 3 new products (A, C, E)"
assert duplicate_count == 2, "Should have 2 duplicates (B, D)"

print("\n✅ Test Case 3 PASSED")

print("\n" + "=" * 60)
print("All tests passed! Bulk add logic is correct.")
print("=" * 60)
