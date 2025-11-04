"""
PowerPoint Proposal Generation Module
Handles slide cloning, table updates, and presentation assembly for Phase 2.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from typing import List, Dict, Optional
import io
import copy
from datetime import datetime
import pandas as pd
import math


def calculate_moq(estimated_unit_price):
    """Calculate MOQ based on $1000 minimum order value using ceiling."""
    if estimated_unit_price <= 0:
        return 10
    moq = math.ceil(1000 / estimated_unit_price)
    return moq


def apply_marketing_rounding(price, marketing_rounding_enabled):
    """Apply marketing rounding (charm pricing) if enabled."""
    if not marketing_rounding_enabled:
        return price
    if price % 10 == 0 and price > 10:
        return price - 1
    return price


def clean_price(value):
    """Convert price string to float."""
    if pd.isna(value) or value == '':
        return 0.0
    if isinstance(value, str):
        value = value.replace('$', '').replace(',', '').strip()
        try:
            return float(value)
        except:
            return 0.0
    return float(value)


def calculate_proposal_pricing(proposal_item: Dict, get_unit_price_func, marketing_rounding: bool, discount_percent: float) -> Dict:
    """
    Calculate all pricing data for a proposal item.
    Replicates the logic from app.py lines 1033-1090.

    Returns dict with: moq, moq_price_per_unit, client_price, delivery_time, customization_setup_fee, customization_per_unit
    """
    product_row = pd.Series(proposal_item['product_data'])
    markup_percent = proposal_item['markup_percent']

    # Calculate MOQ using standard preliminary quantity (100 units)
    preliminary_base_price, _, _ = get_unit_price_func(product_row, 100)

    if preliminary_base_price is None:
        return None

    # Estimate total per-unit price with markup
    temp_markup_multiplier = 1 + (markup_percent / 100)
    estimated_unit_price = preliminary_base_price * temp_markup_multiplier

    # Calculate MOQ
    moq = calculate_moq(estimated_unit_price)
    if moq is None:
        moq = 5

    # Get actual base price for MOQ quantity
    moq_base_price, moq_tier_range, _ = get_unit_price_func(product_row, moq)

    if moq_base_price is None:
        return None

    # Calculate product price WITHOUT customization
    moq_product_cost = moq_base_price * moq
    moq_markup_amount = moq_product_cost * (markup_percent / 100)
    moq_product_only_total = moq_product_cost + moq_markup_amount
    moq_product_price_per_unit = moq_product_only_total / moq

    # Apply marketing rounding if enabled
    if marketing_rounding:
        moq_product_price_per_unit = apply_marketing_rounding(moq_product_price_per_unit, True)

    # Calculate client price (with discount)
    client_price = moq_product_price_per_unit
    if discount_percent > 0:
        client_price = moq_product_price_per_unit * (1 - discount_percent / 100)

    # Get customization costs from product data
    setup_fee = clean_price(product_row.get('Customization Setup Fee', '')) or 0.0
    per_unit_cost = clean_price(product_row.get('Customization Cost per Unit', '')) or 0.0

    # Get delivery time (default to 6-8 weeks)
    delivery_time = product_row.get('Lead Time', '6-8 weeks')
    if pd.isna(delivery_time) or not delivery_time:
        delivery_time = '6-8 weeks'

    return {
        'moq': moq,
        'moq_price_per_unit': moq_product_price_per_unit,
        'client_price': client_price,
        'delivery_time': delivery_time,
        'customization_setup_fee': setup_fee,
        'customization_per_unit': per_unit_cost
    }


def update_cell_text_preserve_format(cell, new_text: str):
    """
    Update table cell text while preserving original font formatting.

    Args:
        cell: Table cell object
        new_text: New text to insert
    """
    # Access the text frame
    text_frame = cell.text_frame

    # Clear existing paragraphs but keep the first one for formatting reference
    if len(text_frame.paragraphs) > 0:
        # Get original font properties from first run (if exists)
        original_font = None
        if len(text_frame.paragraphs[0].runs) > 0:
            original_font = text_frame.paragraphs[0].runs[0].font

        # Clear all text
        text_frame.clear()

        # Add new paragraph with new text
        p = text_frame.paragraphs[0]
        run = p.add_run()
        run.text = new_text

        # Apply original font properties if they existed
        if original_font:
            if original_font.size:
                run.font.size = original_font.size
            if original_font.name:
                run.font.name = original_font.name
            if original_font.bold is not None:
                run.font.bold = original_font.bold
            if original_font.italic is not None:
                run.font.italic = original_font.italic
            if original_font.color.rgb:
                run.font.color.rgb = original_font.color.rgb
    else:
        # Fallback if no paragraphs exist
        cell.text = new_text


def find_slide_by_product_name(prs: Presentation, product_name: str) -> Optional[int]:
    """
    Find slide index by matching product name in first shape.

    Args:
        prs: Presentation object
        product_name: Product name to find (from confirmed_matches)

    Returns:
        Slide index (int) or None if not found
    """
    for idx, slide in enumerate(prs.slides):
        if len(slide.shapes) >= 1:
            first_shape = slide.shapes[0]
            if hasattr(first_shape, "text") and first_shape.text.strip():
                if first_shape.text.strip() == product_name:
                    return idx
    return None


def clone_slide(prs: Presentation, slide_index: int) -> object:
    """
    Clone a slide from presentation, preserving all formatting.
    Uses XML deep copy approach to preserve all elements.

    Args:
        prs: Presentation object
        slide_index: Index of slide to clone (0-based)

    Returns:
        Cloned slide object
    """
    # Get source slide
    slide_list = list(prs.slides)
    source_slide = slide_list[slide_index]

    # Get blank layout (typically index 6, but we'll use the source slide's layout)
    source_layout = source_slide.slide_layout

    # Add new slide with same layout
    new_slide = prs.slides.add_slide(source_layout)

    # Remove all default shapes from new slide
    for shape in list(new_slide.shapes):
        sp = shape.element
        sp.getparent().remove(sp)

    # Copy all shapes from source to new slide
    for shape in source_slide.shapes:
        el = shape.element
        newel = copy.deepcopy(el)
        new_slide.shapes._spTree.insert_element_before(newel, 'p:extLst')

    return new_slide


def update_pricing_table(slide: object, proposal_item: Dict) -> bool:
    """
    Update pricing table in slide with proposal data.
    Handles 3 table formats: 2x3, 2x4, 3x4

    Args:
        slide: Slide object with table
        proposal_item: Dict with calculated pricing data

    Returns:
        True if table was updated, False if no table found
    """
    # Find table in slide
    table = None
    for shape in slide.shapes:
        if shape.has_table:
            table = shape.table
            break

    if not table:
        return False

    # Get proposal data
    moq = proposal_item.get('moq', 10)
    base_price = proposal_item.get('moq_price_per_unit', 0)
    client_price = proposal_item.get('client_price', base_price)
    delivery_time = proposal_item.get('delivery_time', '6-8 weeks')
    setup_fee = proposal_item.get('customization_setup_fee', 0)
    per_unit_cost = proposal_item.get('customization_per_unit', 0)

    # Format prices
    base_price_str = f"${base_price:.2f}"
    client_price_str = f"${client_price:.2f}"

    # Detect table format
    rows = len(table.rows)
    cols = len(table.columns)

    # Update based on format
    if rows >= 2:
        # Update MOQ (Row 1, Col 0)
        update_cell_text_preserve_format(table.cell(1, 0), str(moq))

        if cols == 3:
            # Format 2x3: MOQ | Price Ea | Delivery
            # Use client price (with discount if applicable)
            update_cell_text_preserve_format(table.cell(1, 1), client_price_str)
            update_cell_text_preserve_format(table.cell(1, 2), delivery_time)

            # Update header for price column
            update_cell_text_preserve_format(table.cell(0, 1), f"Price Ea\n(@ Qty {moq})")

        elif cols == 4:
            # Format 2x4 or 3x4: MOQ | Base Price | Client Price | Delivery
            # Column 1: Base price (with markup, no discount)
            update_cell_text_preserve_format(table.cell(1, 1), base_price_str)

            # Column 2: Client price (with discount if applicable)
            update_cell_text_preserve_format(table.cell(1, 2), client_price_str)

            # Column 3: Delivery
            update_cell_text_preserve_format(table.cell(1, 3), delivery_time)

            # Update headers
            update_cell_text_preserve_format(table.cell(0, 0), "MOQ")
            update_cell_text_preserve_format(table.cell(0, 1), f"Price Ea\n(@ Qty {moq})")

            # Build client price header based on whether discount is applied
            if client_price < base_price:
                # Discount was applied
                discount_pct = ((base_price - client_price) / base_price) * 100
                update_cell_text_preserve_format(table.cell(0, 2), f"Client Price\n({discount_pct:.0f}% discount)")
            else:
                # No discount
                update_cell_text_preserve_format(table.cell(0, 2), f"Client Price\n(@ Qty {moq})")

            update_cell_text_preserve_format(table.cell(0, 3), "Delivery\n(after art ✓)")

    # Update customization row if it exists (3x4 format)
    if rows >= 3 and (setup_fee > 0 or per_unit_cost > 0):
        # Format customization text
        if per_unit_cost > 0:
            customization_text = f"Artwork set-up: ${setup_fee:.2f} / Engraving per piece: From ${per_unit_cost:.2f}"
        else:
            customization_text = f"Artwork set-up: ${setup_fee:.2f}"

        # Update Row 2, Col 0 (customization row typically spans columns)
        update_cell_text_preserve_format(table.cell(2, 0), customization_text)

    return True


def add_cover_slide(prs: Presentation, client_name: str, date_str: str) -> object:
    """
    Add cover slide to beginning of presentation.

    Args:
        prs: Presentation object
        client_name: Company name from order details
        date_str: Formatted date string

    Returns:
        Cover slide object
    """
    # Use title slide layout (typically index 0)
    title_layout = prs.slide_layouts[0]

    # Add slide at beginning
    slide = prs.slides.add_slide(title_layout)

    # Set title and subtitle
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = f"Product Proposal for {client_name}"
    subtitle.text = f"Peace by Piece International\n{date_str}"

    # Move to beginning
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    xml_slides.remove(slides[-1])
    xml_slides.insert(0, slides[-1])

    return slide


def create_proposal_presentation(
    template_path: str,
    confirmed_matches: Dict[str, str],
    proposal_products: List[Dict],
    get_unit_price_func,
    marketing_rounding: bool = False,
    discount_percent: float = 0.0
) -> Presentation:
    """
    Create new presentation with only confirmed product slides.
    Strategy: Load template, keep only needed slides, update pricing tables.

    Args:
        template_path: Path to "November All Slides.pptx"
        confirmed_matches: Dict of {gs_product_name: pptx_product_name}
        proposal_products: List of proposal items from session state
        get_unit_price_func: Function to calculate unit prices
        marketing_rounding: Whether to apply marketing rounding
        discount_percent: Discount percentage to apply

    Returns:
        New Presentation object with selected and updated slides
    """
    # Load template (we'll modify this directly)
    prs = Presentation(template_path)

    # Find slide indices to keep and their proposal data
    slides_to_keep = {}  # {slide_idx: proposal_item}

    for gs_name, pptx_name in confirmed_matches.items():
        # Find slide in template
        slide_idx = find_slide_by_product_name(prs, pptx_name)

        if slide_idx is not None:
            # Find matching proposal item
            proposal_item = next(
                (item for item in proposal_products
                 if item['product_data']['Product/Service'] == gs_name),
                None
            )

            slides_to_keep[slide_idx] = proposal_item

    # Remove slides we don't need (work backwards to preserve indices)
    slide_list = list(prs.slides)
    for idx in range(len(slide_list) - 1, -1, -1):
        if idx not in slides_to_keep:
            # Remove this slide
            rId = prs.slides._sldIdLst[idx].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[idx]

    # Update pricing tables in remaining slides
    # Note: After deletion, slide indices change, so we need to match by name
    for slide in prs.slides:
        # Get product name from first shape
        if len(slide.shapes) >= 1:
            first_shape = slide.shapes[0]
            if hasattr(first_shape, "text") and first_shape.text.strip():
                product_name = first_shape.text.strip()

                # Find the proposal item for this slide
                for gs_name, pptx_name in confirmed_matches.items():
                    if pptx_name == product_name:
                        # Find proposal item
                        proposal_item = next(
                            (item for item in proposal_products
                             if item['product_data']['Product/Service'] == gs_name),
                            None
                        )

                        if proposal_item:
                            # Calculate pricing data
                            pricing_data = calculate_proposal_pricing(
                                proposal_item,
                                get_unit_price_func,
                                marketing_rounding,
                                discount_percent
                            )

                            if pricing_data:
                                update_pricing_table(slide, pricing_data)
                        break

    return prs


def download_presentation(prs: Presentation, client_name: str) -> io.BytesIO:
    """
    Convert presentation to bytes and return for download.

    Args:
        prs: Presentation object
        client_name: For filename generation

    Returns:
        BytesIO object for st.download_button
    """
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output
