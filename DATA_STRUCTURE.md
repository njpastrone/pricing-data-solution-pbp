# DATA_STRUCTURE.md

**Reference document for jaggery_sample_6_23 Google Sheet structure**

This file documents the exact structure of our pricing data to prevent coding mistakes and ensure consistent data handling throughout the project.

---

## Sheet Overview

- **Sheet Name:** jaggery_sample_6_23
- **Total Rows:** ~1000
- **Total Columns:** 25
- **Data Starts:** Row 6 (after header rows)
- **Header Row:** Row 5

---

## Sheet Structure

### Rows 1-5: Header Section
- **Row 1:** Contains "STATUS" label (column B)
- **Row 2:** Contains "Active" status (column B)
- **Row 3:** Empty row
- **Row 4:** Section headers - "PRODUCT DETAILS" (column A) and "COST INFORMATION" (column K)
- **Row 5:** Column headers (the actual field names we use)

### Row 6 onwards: Product Data

---

## Column Mapping (Row 5 Headers)

| Column Index | Column Letter | Field Name | Description |
|--------------|---------------|------------|-------------|
| 0 | A | Product Ref. No. | Unique product reference (e.g., JA01, JA02) |
| 1 | B | Artisan Partner | Partner name (e.g., Jaggery) |
| 2 | C | Origin Country | Country of origin (e.g., India) |
| 3 | D | Gift Name | Product name/title |
| 4 | E | Representative Image | Image reference |
| 5 | F | Dimension | Product dimensions |
| 6 | G | Description | Full product description |
| 7 | H | Partner Info | Information about the artisan partner |
| 8 | I | Material(s) Options | Material options (e.g., canvas, cargo, seat) |
| 9 | J | Minimum Qty | Minimum order quantity |
| 10 | K | PBP Cost w/o shipping (-25) | Cost for less than 25 units |
| 11 | L | Jaggery Price Update 6_23 | Updated pricing from June 2023 |
| 12 | M | PBP Cost w/o shipping (1-25) | Cost for 1-25 units |
| 13 | N | PBP Cost w/o shipping (26-50) | Cost for 26-50 units |
| 14 | O | PBP Cost w/o shipping (51-100) | Cost for 51-100 units |
| 15 | P | PBP Cost w/o shipping (101-250) | Cost for 101-250 units |
| 16 | Q | PBP Cost w/o shipping (251-500) | Cost for 251-500 units |
| 17 | R | PBP Cost w/o shipping (501-1000) | Cost for 501-1000 units |
| 18 | S | PBP Cost w/o shipping (1000+) | Cost for 1000+ units |
| 19 | T | Art Setup Fee | Setup fee for artwork/customization |
| 20 | U | Labels up to 1" x 2.5' | Label cost |
| 21 | V | Minimum for labels | Minimum quantity for labels |

---

## Sample Data (Row 6)

```
Product Ref. No.: JA01
Artisan Partner: Jaggery
Origin Country: India
Gift Name: Upcycled Pilot's Everyday Case
Dimension: 13" X 13" X 4". Shoulder strap (45"). Exterior pockets (8" x 9" x 1").
PBP Cost w/o shipping (-25): $55.00
Jaggery Price Update 6_23: $48.00
PBP Cost w/o shipping (1-25): $48.00
PBP Cost w/o shipping (26-50): $40.80
PBP Cost w/o shipping (51-100): $38.40
PBP Cost w/o shipping (501-1000): $36.00
Art Setup Fee: 70
Labels up to 1" x 2.5': 1.5
Minimum for labels: 100
```

---

## Important Data Characteristics

### 1. **Tiered Pricing Structure**
- Products have **quantity-based pricing tiers**
- Different costs for different quantity ranges: 1-25, 26-50, 51-100, 101-250, 251-500, 501-1000, 1000+
- Not all tiers may have values for all products (some cells may be empty)

### 2. **Empty Cells**
- Some pricing tiers may be blank/empty
- Optional fields like materials, images may be empty

### 3. **Currency Format**
- Prices include "$" symbol and are formatted as currency (e.g., "$48.00")
- Need to strip "$" and convert to float for calculations

### 4. **Header Rows to Skip**
- When reading data, **skip rows 1-5**
- Row 5 contains the actual column headers
- Data starts at row 6

### 5. **Long Text Fields**
- Description and Partner Info contain very long text
- May include newlines and special characters

---

## How to Read This Data in Code

### Option 1: Skip header rows and use row 5 as headers
```python
sheet = gc.open("jaggery_sample_6_23").sheet1
all_values = sheet.get_all_values()
headers = all_values[4]  # Row 5 (index 4)
data_rows = all_values[5:]  # Row 6 onwards (index 5+)
```

### Option 2: Use pandas with skiprows
```python
import pandas as pd
# Skip first 5 rows, use row 5 as header
df = pd.DataFrame(data_rows, columns=headers)
```

---

## Key Fields for MVP

For the initial MVP, focus on these essential fields:

1. **Product Ref. No.** - Unique identifier
2. **Artisan Partner** - Partner name
3. **Gift Name** - Product name
4. **Pricing Tiers** (columns 10-18) - Quantity-based pricing
5. **Art Setup Fee** - Additional customization cost
6. **Minimum Qty** - Minimum order quantity

---

## Notes

- This structure is significantly different from `master_pricing_demo` which had a simple flat structure
- The real data uses **tiered pricing** based on order quantity
- Need to implement **quantity-based price selection** logic
- Current MVP app will need substantial updates to handle this structure
- Price format requires cleaning (remove "$" and convert to float)

---

**Last Updated:** 2025-10-02
**Data Source:** jaggery_sample_6_23 Google Sheet
