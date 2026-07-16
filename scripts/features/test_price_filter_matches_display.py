"""
Verify the Tab 1 price-range filter matches the client price shown in the catalog.

Reproduces the team-reported bug: filtering for gifts under $30 returned products
that display above $30. Root cause was that the filter used a simpler
"Vendor MSRP or cost x2" estimate that ignored add-ons and used a different
quantity than the price actually displayed/quoted.

The fix routes both the catalog display and the filter through
calculate_catalog_client_price() so they use the same number.

Run: python scripts/features/test_price_filter_matches_display.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.pricing_engine import (
    calculate_pbp_msrp,
    calculate_catalog_client_price,
    get_unit_price_new_system,
)
from src.helpers import calculate_moq, clean_price, get_column_value


def old_filter_price(row):
    """The OLD filter logic (before the fix), reproduced here for comparison."""
    msrp_raw = get_column_value(row, "Vendor Published MSRP", "MSRP", "")
    msrp = clean_price(msrp_raw) if msrp_raw and str(msrp_raw).strip() not in ["nan", "", "0", "0.0"] else None
    if msrp and msrp > 0:
        return msrp
    base_cost, _, _ = get_unit_price_new_system(row, 100)
    if not base_cost:
        return None
    return base_cost * 2


def displayed_price(row):
    """The price the catalog actually shows (PBP MSRP at the product's MOQ)."""
    prelim = calculate_pbp_msrp(dict(row), quantity=100)
    pbp_msrp = prelim["pbp_msrp"]
    if not pbp_msrp:
        return None
    moq = calculate_moq(pbp_msrp, row)["moq"]
    return calculate_pbp_msrp(dict(row), quantity=moq)["pbp_msrp"]


# --- Test products -----------------------------------------------------------
# Product 1: "MSRP + % of cost" with add-ons. Vendor MSRP is $29 (under $30),
# but the client price adds a per-cost add-on, pushing it OVER $30.
# This is the exact shape of the reported bug.
product_addon = {
    "Product/Service": "Add-on Gift",
    "Partner": "Test",
    "Pricing Tiers (Y/N)": "N",
    "PBP Cost (No Tiers/Tier 1)": "20.00",
    "Units per Case": 1,
    "Vendor Published MSRP": "29.00",
    "Pricing Logic": "MSRP + % of cost",
    "Shipping Add-On % (of Cost)": "30",   # 30% of $20 cost = $6 add-on -> $35 client price
    "Other Add-On % (of Cost)": "0",
    "Cost Basis (Per Item/Per Case)": "Per Item",
}

# Product 2: Standard markup, no MSRP. Cost x2 at qty 100 is cheap, but the
# product is tiered and its MOQ quantity lands in a pricier tier.
product_tiered = {
    "Product/Service": "Tiered Gift",
    "Partner": "Test",
    "Pricing Tiers (Y/N)": "Y",
    "Pricing Tiers Info": "T1: 1-50, T2: 51-100, T3: 101+",
    "PBP Cost (No Tiers/Tier 1)": "16.00",   # Tier 1 (1-50): $16 -> client $32
    "PBP Cost: Tier 2": "14.00",             # Tier 2 (51-100): $14 -> client $28
    "PBP Cost: Tier 3": "12.00",
    "Units per Case": 1,
    "Vendor Published MSRP": "",
    "Pricing Logic": "Standard markup",
    "Cost Basis (Per Item/Per Case)": "Per Item",
}

# Product 3: "MSRP capped" - client price IS the vendor MSRP. Old and new agree.
product_capped = {
    "Product/Service": "Capped Gift",
    "Partner": "Test",
    "Pricing Tiers (Y/N)": "N",
    "PBP Cost (No Tiers/Tier 1)": "10.00",
    "Units per Case": 1,
    "Vendor Published MSRP": "25.00",
    "Pricing Logic": "MSRP capped – ship absorbed",
    "Cost Basis (Per Item/Per Case)": "Per Item",
}


def check(product, max_budget=30.0):
    name = product["Product/Service"]
    shown = displayed_price(product)
    new_filter = calculate_catalog_client_price(product)["client_price"]
    old = old_filter_price(product)

    # The new filter price MUST equal the price the catalog displays.
    assert abs(new_filter - shown) < 0.01, (
        f"{name}: new filter price ${new_filter:.2f} != displayed ${shown:.2f}"
    )

    old_passes = old is not None and old <= max_budget
    new_passes = new_filter <= max_budget
    shown_ok = shown <= max_budget

    # The new filter's include/exclude decision MUST agree with the shown price.
    assert new_passes == shown_ok, (
        f"{name}: new filter pass={new_passes} but shown-under-budget={shown_ok}"
    )

    print(f"{name}:")
    print(f"  displayed client price : ${shown:.2f}")
    print(f"  OLD filter price       : ${old:.2f}  -> under ${max_budget:.0f}? {old_passes}")
    print(f"  NEW filter price       : ${new_filter:.2f}  -> under ${max_budget:.0f}? {new_passes}")
    print(f"  correct (matches shown): {new_passes == shown_ok}")
    print()
    return old_passes, new_passes, shown_ok


print("=" * 70)
print("Price filter vs displayed price - bug reproduction & fix verification")
print("Budget: gifts under $30")
print("=" * 70)
print()

# Product 1: the reported bug. Old filter wrongly INCLUDES it (sees $29 MSRP),
# but it displays at $35. New filter correctly EXCLUDES it.
old1, new1, shown1 = check(product_addon)
assert old1 is True, "Expected OLD filter to wrongly include the add-on product (the bug)"
assert new1 is False, "Expected NEW filter to correctly exclude the add-on product"
assert shown1 is False, "Add-on product should display above $30"

# Product 2: tiered. Old filter uses qty-100 tier ($14 -> $28), includes it,
# but at its MOQ the product displays at a higher tier.
old2, new2, shown2 = check(product_tiered)
assert new2 == shown2, "New filter must agree with displayed price for tiered product"

# Product 3: capped MSRP - old and new both correctly include ($25 < $30).
old3, new3, shown3 = check(product_capped)
assert new3 is True and shown3 is True, "Capped $25 product should pass a <$30 filter"

print("=" * 70)
print("ALL CHECKS PASSED")
print("- Reported bug reproduced with OLD logic (over-$30 product slipped through)")
print("- NEW filter price equals the displayed catalog price for every product")
print("- NEW filter include/exclude decision matches what the client sees")
print("=" * 70)
