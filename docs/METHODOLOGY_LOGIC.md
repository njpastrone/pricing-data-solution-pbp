# Methodology & Calculation Logic

**Purpose:** Document all pricing methodologies, calculations, and business rules for each partner

**Created:** 2025-10-02

**Important:** Different partners have different pricing rules. This document tracks all methodologies to ensure accurate quote calculations.

---

## 📐 Core Calculation Formula

### Master Quote Calculation Formula

```
Total Quote = (Product Costs + Additional Costs + Markup) + Shipping + Tariff

Where:
- Product Costs = Base Price × Quantity
- Additional Costs = Art Setup Fee + Label Costs (if applicable)
- Markup = Product Costs × (Markup % / 100)
- Shipping = Total shipping cost for entire order
- Tariff = Total tariff/duty cost for entire order
```

### Per-Unit Breakdown Formula

```
Total Per Unit = Base Price + (Art Setup / Quantity) + (Label Costs / Quantity) + Markup Per Unit + (Shipping / Quantity) + (Tariff / Quantity)

Where:
- Markup Per Unit = Base Price × (Markup % / 100)
```

---

## 🏭 Partner-Specific Methodologies

### Partner: Jaggery

**Data Source:** jaggery_demo Google Sheet

#### 1. Tiered Pricing Structure

**Tier Selection Logic:**
- Base price varies by order quantity
- 7 pricing tiers based on quantity ranges

| Quantity Range | Column Name | Example Price |
|----------------|-------------|---------------|
| 1-25 units | PBP Cost w/o shipping (1-25) | $48.00 |
| 26-50 units | PBP Cost w/o shipping (26-50) | $40.80 |
| 51-100 units | PBP Cost w/o shipping (51-100) | $38.40 |
| 101-250 units | PBP Cost w/o shipping (101-250) | (varies) |
| 251-500 units | PBP Cost w/o shipping (251-500) | (varies) |
| 501-1000 units | PBP Cost w/o shipping (501-1000) | (varies) |
| 1000+ units | PBP Cost w/o shipping (1000+) | $36.00 |

**Business Rule:**
- Use the tier that matches the order quantity
- If a tier is missing data, fall back to next available tier (higher tier preferred for conservative pricing)

#### 2. Art Setup Fee

**Rule:** One-time fee per order (NOT per unit)

**Calculation:**
```
Art Setup Fee Total = Value from "Art Setup Fee" column (e.g., $70)
Art Setup Fee Per Unit = Art Setup Fee Total / Quantity
```

**Example:**
- Product: JA01 (Upcycled Pilot's Everyday Case)
- Art Setup Fee: $70
- Order: 50 units
- Calculation:
  - Total art setup: $70
  - Per unit: $70 / 50 = $1.40 per unit

**Display in Quote:**
- Show as separate line item: "Art Setup Fee: $70.00"
- Include in per-unit breakdown: "Art Setup (per unit): $1.40"

#### 3. Label Costs

**Rule:** Optional - customer chooses whether to add labels

**Components:**
1. **Label Art Setup Fee:** $70 (one-time per order)
2. **Label Unit Cost:** From "Labels up to 1\" x 2.5'" column (e.g., $1.50 per label)
3. **Minimum Quantity:** From "Minimum for labels" column (typically 100 labels)

**Business Rule - Label Minimum:**
- If customer orders **fewer than minimum** BUT wants labels:
  - Customer still pays for **minimum number of labels**
- If customer orders **more than minimum**:
  - Customer pays for **actual number of units ordered**

**Calculation Logic:**
```python
if customer_wants_labels:
    label_art_setup = 70  # Jaggery-specific
    label_unit_cost = 1.50  # From product data
    label_minimum = 100  # From product data

    # Apply minimum
    labels_to_charge = max(order_quantity, label_minimum)

    # Calculate costs
    label_setup_total = 70
    label_cost_total = label_unit_cost × labels_to_charge
    total_label_cost = label_setup_total + label_cost_total

    # Per-unit calculation
    label_cost_per_unit = total_label_cost / order_quantity
```

**Example 1: Order Below Minimum**
- Product: JA01
- Order Quantity: 50 units
- Customer wants labels: YES
- Label unit cost: $1.50
- Label minimum: 100

Calculation:
```
Label Art Setup: $70
Labels to charge: max(50, 100) = 100 labels
Label Cost: $1.50 × 100 = $150
Total Label Cost: $70 + $150 = $220

Per Unit (for 50 units):
Label Cost Per Unit: $220 / 50 = $4.40 per unit
```

**Example 2: Order Above Minimum**
- Product: JA01
- Order Quantity: 150 units
- Customer wants labels: YES
- Label unit cost: $1.50
- Label minimum: 100

Calculation:
```
Label Art Setup: $70
Labels to charge: max(150, 100) = 150 labels
Label Cost: $1.50 × 150 = $225
Total Label Cost: $70 + $225 = $295

Per Unit (for 150 units):
Label Cost Per Unit: $295 / 150 = $1.97 per unit
```

**Example 3: No Labels**
- Order Quantity: 50 units
- Customer wants labels: NO

Calculation:
```
Label Art Setup: $0
Label Cost: $0
Total Label Cost: $0
```

**User Interface:**
- Include checkbox: "Add custom labels to this order"
- If checked AND quantity < minimum:
  - Show warning: "⚠️ Minimum 100 labels required. You'll be charged for 100 labels even though ordering 50 units."
- Display label costs as separate line items in quote breakdown

#### 4. Currency Handling

**Data Format:** Prices stored with "$" symbol (e.g., "$48.00")

**Processing:**
```python
def clean_price(price_string):
    """Convert '$48.00' or '$1,500.00' to float"""
    if not price_string or price_string == '':
        return None
    # Remove $, commas, whitespace
    cleaned = price_string.replace('$', '').replace(',', '').strip()
    return float(cleaned)
```

#### 5. Minimum Order Quantity

**Rule:** Some products may have minimum order quantities

**Data Field:** "Minimum Qty" column

**Business Logic:**
- If user enters quantity below minimum:
  - Show warning: "⚠️ Minimum order quantity for this product is X units"
  - Allow order to proceed (user may negotiate with partner)
  - Do NOT block the quote generation

---

## 📊 Complete Quote Calculation Example

### Example: JA01 - 50 units with labels

**Product Data:**
- Product: JA01 - Upcycled Pilot's Everyday Case
- Partner: Jaggery
- Quantity: 50 units
- Tier: 26-50 units → $40.80 per unit
- Art Setup Fee: $70
- Customer wants labels: YES
- Label cost: $1.50 per label
- Label minimum: 100 labels

**User Inputs:**
- Markup: 100% (2x)
- Shipping: $200
- Tariff: $100

**Calculation Breakdown:**

**Step 1: Product Costs**
```
Base Price (26-50 tier): $40.80
Quantity: 50 units
Product Subtotal: $40.80 × 50 = $2,040.00
```

**Step 2: Additional Costs**
```
Art Setup Fee: $70.00

Label Costs:
- Label Art Setup: $70.00
- Labels to charge: max(50, 100) = 100 labels
- Label Cost: $1.50 × 100 = $150.00
- Total Label Cost: $70 + $150 = $220.00

Total Additional Costs: $70 + $220 = $290.00
```

**Step 3: Subtotal Before Markup**
```
Subtotal: $2,040.00 + $290.00 = $2,330.00
```

**Step 4: Apply Markup**
```
Markup %: 100%
Markup applies to: Product Subtotal only ($2,040.00)
Markup Amount: $2,040.00 × 1.00 = $2,040.00
Subtotal After Markup: $2,040.00 + $2,040.00 = $4,080.00
```

**Step 5: Add Shipping and Tariff**
```
Subtotal After Markup: $4,080.00
Additional Costs (already included): $290.00
Shipping: $200.00
Tariff: $100.00

Total Quote: $4,080.00 + $290.00 + $200.00 + $100.00 = $4,670.00
```

**Per-Unit Breakdown:**
```
Base Price: $40.80
Art Setup (per unit): $70 / 50 = $1.40
Label Cost (per unit): $220 / 50 = $4.40
Markup (per unit): $40.80 × 1.00 = $40.80
Shipping (per unit): $200 / 50 = $4.00
Tariff (per unit): $100 / 50 = $2.00

Total Per Unit: $40.80 + $1.40 + $4.40 + $40.80 + $4.00 + $2.00 = $93.40
Verification: $93.40 × 50 = $4,670.00 ✅
```

**Quote Display:**

| Cost Component | Per Unit | Total |
|----------------|----------|-------|
| Base Price (26-50 tier) | $40.80 | $2,040.00 |
| Art Setup Fee | $1.40 | $70.00 |
| Label Art Setup | $1.40 | $70.00 |
| Labels (100 @ $1.50) | $3.00 | $150.00 |
| **Subtotal** | **$46.60** | **$2,330.00** |
| Markup (100%) | $40.80 | $2,040.00 |
| **Subtotal After Markup** | **$87.40** | **$4,370.00** |
| Shipping | $4.00 | $200.00 |
| Tariff | $2.00 | $100.00 |
| **TOTAL** | **$93.40** | **$4,670.00** |

**Important Notes:**
- ⚠️ Label minimum applies: Ordering 50 units but paying for 100 labels
- Markup applies to base product price only, NOT to setup fees, labels, shipping, or tariff
- All setup fees are one-time per order

---

## 🔧 Implementation Notes

### Partner Configuration Structure (Future)

When adding multiple partners, use this structure:

```python
PARTNER_CONFIG = {
    'jaggery': {
        'tier_columns': [
            {'min': 1, 'max': 25, 'column': 'PBP Cost w/o shipping (1-25)'},
            {'min': 26, 'max': 50, 'column': 'PBP Cost w/o shipping (26-50)'},
            {'min': 51, 'max': 100, 'column': 'PBP Cost w/o shipping (51-100)'},
            {'min': 101, 'max': 250, 'column': 'PBP Cost w/o shipping (101-250)'},
            {'min': 251, 'max': 500, 'column': 'PBP Cost w/o shipping (251-500)'},
            {'min': 501, 'max': 1000, 'column': 'PBP Cost w/o shipping (501-1000)'},
            {'min': 1001, 'max': float('inf'), 'column': 'PBP Cost w/o shipping (1000+)'}
        ],
        'art_setup_column': 'Art Setup Fee',
        'label_config': {
            'art_setup_fee': 70,
            'unit_cost_column': 'Labels up to 1" x 2.5\'',
            'minimum_column': 'Minimum for labels',
            'default_minimum': 100
        },
        'columns': {
            'partner': 'Artisan Partner',
            'product': 'Gift Name',
            'product_ref': 'Product Ref. No.',
            'minimum_qty': 'Minimum Qty'
        }
    },
    'partner_b': {
        # Different configuration for another partner
        'tier_columns': [
            {'min': 1, 'max': 50, 'column': 'Price Tier 1'},
            {'min': 51, 'max': 100, 'column': 'Price Tier 2'}
        ],
        # ... other config
    }
}
```

### Markup Application Rule

**IMPORTANT:** Markup applies to **product base price only**

**DO apply markup to:**
- Base price from tier

**DO NOT apply markup to:**
- Art setup fees
- Label setup fees
- Label costs
- Shipping
- Tariff

This is a standard wholesale/retail pricing practice where markup is applied to the cost of goods, not to additional fees or logistics costs.

---

## 🧪 Test Cases

### Test Case 1: Basic Order (No Labels)
- Product: JA01
- Quantity: 75 (tier: 51-100 @ $38.40)
- Art Setup: $70
- Labels: NO
- Markup: 100%
- Shipping: $150
- Tariff: $50

**Expected:**
```
Product: $38.40 × 75 = $2,880.00
Art Setup: $70
Subtotal: $2,950.00
Markup (on $2,880 only): $2,880.00
Subtotal After Markup: $5,830.00
Shipping: $150
Tariff: $50
TOTAL: $6,030.00
Per Unit: $80.40
```

### Test Case 2: Order with Labels (Above Minimum)
- Product: JA01
- Quantity: 150 (tier: 101-250)
- Labels: YES (minimum 100)
- Expected: Charge for 150 labels (actual quantity)

### Test Case 3: Order with Labels (Below Minimum)
- Product: JA01
- Quantity: 50 (tier: 26-50 @ $40.80)
- Labels: YES (minimum 100)
- Expected: Charge for 100 labels (minimum)
- Warning: "⚠️ Minimum 100 labels required"

### Test Case 4: Missing Tier Fallback
- Product: XYZ
- Quantity: 75 (tier 51-100 is empty)
- Expected: Use next available tier with warning

---

## 🛒 Multi-Product Order Calculations

### Overview
The app supports multi-product orders where users can add multiple products to a single order, each with its own markup percentage. Shipping and tariff costs are applied once at the order level.

### Multi-Product Formula

```
Total Order Quote = Sum(All Product Totals) + Order Shipping + Order Tariff

Where each Product Total:
Product Total = (Base Price × Quantity) + Art Setup + Label Costs + (Markup on Base Price)
```

### Key Rules
1. **Per-Product Markup:** Each product can have a different markup percentage
2. **Order-Level Shipping:** Shipping cost applies once to entire order, not per product
3. **Order-Level Tariff:** Tariff cost applies once to entire order, not per product
4. **Independent Product Calculations:** Each product calculated separately, then summed

### Example: Multi-Product Order

**Order Details:**

**Product 1:** JA01 - Upcycled Pilot's Everyday Case
- Quantity: 50 units
- Tier: 26-50 @ $40.80 per unit
- Markup: 100%
- Labels: Yes (100 labels minimum)
- Art Setup: $70
- Label Setup: $70
- Label Cost: $1.50 × 100 = $150

**Product 2:** JA02 - Different Product
- Quantity: 100 units
- Tier: 51-100 @ $35.00 per unit
- Markup: 120%
- Labels: No
- Art Setup: $70

**Order Settings:**
- Shipping: $300 (entire order)
- Tariff: $150 (entire order)

**Calculation:**

**Product 1 Total:**
```
Base Cost: $40.80 × 50 = $2,040.00
Art Setup: $70.00
Label Costs: $70 + $150 = $220.00
Subtotal: $2,330.00
Markup (100% on base only): $2,040.00 × 1.00 = $2,040.00
Product 1 Total: $4,370.00
```

**Product 2 Total:**
```
Base Cost: $35.00 × 100 = $3,500.00
Art Setup: $70.00
Subtotal: $3,570.00
Markup (120% on base only): $3,500.00 × 1.20 = $4,200.00
Product 2 Total: $7,770.00
```

**Order Total:**
```
Product 1: $4,370.00
Product 2: $7,770.00
Products Subtotal: $12,140.00

Shipping (once): $300.00
Tariff (once): $150.00

TOTAL ORDER: $12,590.00
Total Units: 150
Average Per Unit: $83.93
```

### Important Notes
- Shipping and tariff are **NOT** divided per product
- Shipping and tariff are **NOT** marked up
- Each product can have different markup percentages
- Label minimums apply per product (if labels selected)
- Art setup fees apply per product

---

## 📚 References

- [APP_UPDATE_PLAN.md](APP_UPDATE_PLAN.md) - Implementation plan
- [DATA_STRUCTURE.md](DATA_STRUCTURE.md) - Jaggery data structure
- [PLANNING.md](PLANNING.md) - Project requirements

---

**Last Updated:** 2025-10-03
**Status:** Multi-product ordering implemented and documented
