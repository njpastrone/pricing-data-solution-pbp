"""
Test MSRP markup calculation logic
"""

def calculate_msrp_markup(msrp, cost):
    """
    Calculate the markup percentage required to reach MSRP price.

    Formula: MSRP = cost * (1 + markup/100)
    Therefore: markup = ((MSRP / cost) - 1) * 100

    Args:
        msrp (float): Manufacturer's Suggested Retail Price
        cost (float): Base cost per unit

    Returns:
        float: Required markup percentage, or None if invalid
    """
    if not msrp or msrp <= 0 or not cost or cost <= 0:
        return None

    required_markup = ((msrp / cost) - 1) * 100

    # Don't allow negative markup (below cost)
    return max(0.0, required_markup)


print("Test Case 1: MSRP at 100% markup (2x cost)")
print("=" * 60)
cost = 10.0
msrp = 20.0
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f}")
print(f"Calculated markup: {markup:.2f}%")
print(f"Verification: ${cost:.2f} * (1 + {markup:.2f}/100) = ${cost * (1 + markup/100):.2f}")
assert abs(markup - 100.0) < 0.01, "Should be 100% markup"
assert abs(cost * (1 + markup/100) - msrp) < 0.01, "Should equal MSRP"
print("✅ PASSED\n")

print("Test Case 2: MSRP at 50% markup (1.5x cost)")
print("=" * 60)
cost = 20.0
msrp = 30.0
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f}")
print(f"Calculated markup: {markup:.2f}%")
print(f"Verification: ${cost:.2f} * (1 + {markup:.2f}/100) = ${cost * (1 + markup/100):.2f}")
assert abs(markup - 50.0) < 0.01, "Should be 50% markup"
assert abs(cost * (1 + markup/100) - msrp) < 0.01, "Should equal MSRP"
print("✅ PASSED\n")

print("Test Case 3: MSRP at 200% markup (3x cost)")
print("=" * 60)
cost = 15.0
msrp = 45.0
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f}")
print(f"Calculated markup: {markup:.2f}%")
print(f"Verification: ${cost:.2f} * (1 + {markup:.2f}/100) = ${cost * (1 + markup/100):.2f}")
assert abs(markup - 200.0) < 0.01, "Should be 200% markup"
assert abs(cost * (1 + markup/100) - msrp) < 0.01, "Should equal MSRP"
print("✅ PASSED\n")

print("Test Case 4: MSRP below cost (break-even scenario)")
print("=" * 60)
cost = 50.0
msrp = 40.0
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f} (below cost!)")
print(f"Calculated markup: {markup:.2f}%")
print(f"Expected: 0% (break-even, don't sell below cost)")
assert markup == 0.0, "Should be 0% when MSRP is below cost"
print("✅ PASSED\n")

print("Test Case 5: MSRP exactly at cost (0% markup)")
print("=" * 60)
cost = 25.0
msrp = 25.0
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f}")
print(f"Calculated markup: {markup:.2f}%")
print(f"Verification: ${cost:.2f} * (1 + {markup:.2f}/100) = ${cost * (1 + markup/100):.2f}")
assert markup == 0.0, "Should be 0% markup"
assert abs(cost * (1 + markup/100) - msrp) < 0.01, "Should equal MSRP"
print("✅ PASSED\n")

print("Test Case 6: Invalid inputs (no MSRP)")
print("=" * 60)
cost = 10.0
msrp = None
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: {msrp}")
print(f"Calculated markup: {markup}")
assert markup is None, "Should return None for invalid MSRP"
print("✅ PASSED\n")

print("Test Case 7: Invalid inputs (zero cost)")
print("=" * 60)
cost = 0.0
msrp = 20.0
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f}")
print(f"Calculated markup: {markup}")
assert markup is None, "Should return None for zero cost"
print("✅ PASSED\n")

print("Test Case 8: Real-world example (MSRP = $12.50, Cost = $5.00)")
print("=" * 60)
cost = 5.0
msrp = 12.50
markup = calculate_msrp_markup(msrp, cost)
print(f"Cost: ${cost:.2f}")
print(f"MSRP: ${msrp:.2f}")
print(f"Calculated markup: {markup:.2f}%")
print(f"Verification: ${cost:.2f} * (1 + {markup:.2f}/100) = ${cost * (1 + markup/100):.2f}")
expected_markup = 150.0  # $5 * 2.5 = $12.50
assert abs(markup - expected_markup) < 0.01, f"Should be {expected_markup}% markup"
assert abs(cost * (1 + markup/100) - msrp) < 0.01, "Should equal MSRP"
print("✅ PASSED\n")

print("=" * 60)
print("All tests passed! MSRP markup calculation is correct.")
print("=" * 60)
