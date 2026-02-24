"""
Slide Matcher Module
Intelligent product name matching system with fuzzy matching fallback.

Logic:
1. Try exact match (case-insensitive)
2. If no exact match, use fuzzy matching with confidence threshold
3. Return match result with confidence score for user review

Dependencies:
- thefuzz: Fuzzy string matching library
- rapidfuzz: Fast string matching (auto-installed with thefuzz)
"""

from thefuzz import fuzz, process
from typing import Optional, Dict, List, Tuple
import re
from .match_manager import (
    load_manual_matches,
    get_manual_match
)
from pptx import Presentation


def find_best_match_multi_scorer(
    query: str,
    choices: List[str],
    limit: int = 3
) -> Tuple[str, int, str, List[Tuple[str, int]]]:
    """
    Use multiple fuzzy matching algorithms and return best result.

    Tests 3 different scoring algorithms and returns the match with
    the highest confidence score across all methods.

    Args:
        query: Product name from Google Sheets
        choices: List of product names from PowerPoint
        limit: Number of alternatives to return

    Returns:
        Tuple of (best_match_name, best_score, method_used, alternatives)

    Example:
        >>> find_best_match_multi_scorer("Laptop Sleeve", ["UPCYCLED LAPTOP SLEEVE", "BRIEFCASE"])
        ("UPCYCLED LAPTOP SLEEVE", 85, "token_set_ratio", [("BRIEFCASE", 20)])
    """
    scorers = [
        ('token_sort_ratio', fuzz.token_sort_ratio),
        ('token_set_ratio', fuzz.token_set_ratio),
        ('partial_ratio', fuzz.partial_ratio),
    ]

    best_overall_match = None
    best_overall_score = 0
    best_method = None
    all_alternatives = {}  # {name: best_score_seen}

    # Try each scoring method
    for method_name, scorer_func in scorers:
        matches = process.extract(
            query,
            choices,
            scorer=scorer_func,
            limit=limit
        )

        if matches:
            # Check if this method found a better match
            top_match_name, top_match_score = matches[0]
            if top_match_score > best_overall_score:
                best_overall_match = top_match_name
                best_overall_score = top_match_score
                best_method = method_name

            # Track all alternatives (keep highest score for each name)
            for match_name, match_score in matches:
                if match_name not in all_alternatives or match_score > all_alternatives[match_name]:
                    all_alternatives[match_name] = match_score

    # Build alternatives list (exclude best match, sort by score, limit to 'limit' items)
    alternatives = [
        (name, score) for name, score in all_alternatives.items()
        if name != best_overall_match
    ]
    alternatives.sort(key=lambda x: x[1], reverse=True)
    alternatives = alternatives[:limit]

    return best_overall_match, best_overall_score, best_method, alternatives


# Category keywords for boosting match confidence
CATEGORY_KEYWORDS = {
    'bags': ['BAG', 'BACKPACK', 'TOTE', 'BRIEFCASE', 'SLEEVE', 'POUCH'],
    'cutting_boards': ['CUTTING', 'BOARD', 'BUTCHER', 'BLOCK'],
    'candles': ['CANDLE', 'HOLDER', 'VOTIVE', 'TEA LIGHT'],
    'trivets': ['TRIVET'],
    'coasters': ['COASTER'],
    'bowls': ['BOWL'],
    'trays': ['TRAY'],
    'jewelry': ['BRACELET', 'NECKLACE', 'EARRING', 'JEWELRY'],
    'home_decor': ['WALL ART', 'PICTURE FRAME', 'VASE', 'PLANTER'],
}

# Keywords that suggest customization/variant (not product categories)
VARIANT_KEYWORDS = ['NOIR', 'MOF', 'LARGE', 'SMALL', 'SET', 'ENFOLD']

# Manual product mappings for known mismatches
# Format: {normalized_gs_name: exact_pptx_name}
# These override fuzzy matching with 100% confidence
MANUAL_PRODUCT_MAPPINGS = {
    'UPCYCLED EXECUTIVE URBAN BRIEFCASE': 'UPCYCLED EXECUTIVE URBAN BRIEFCASE',
    'UPCYCLED LAPTOP SLEEVE': 'UPCYCLED LAPTOP SLEEVE',
    'UPCYCLED DAY TRIPPER BACKPACK': 'UPCYCLED DAY TRIPPER BACKPACK',
    'BUTCHER BLOCK': 'BUTCHER BLOCK',
    'CANDLE HOLDERS': 'MINIMALIST CANDLE HOLDERS – Set of 3',
    # Add more known mappings as discovered during testing
}


def boost_score_if_same_category(
    query: str,
    match: str,
    base_score: int,
    boost_amount: int = 15
) -> int:
    """
    Boost confidence score if query and match share category keywords.

    Args:
        query: Product name from Google Sheets
        match: Product name from PowerPoint
        base_score: Original confidence score (0-100)
        boost_amount: Points to add if same category (default: 15)

    Returns:
        Boosted score (capped at 100)

    Example:
        >>> boost_score_if_same_category("Cutting Board - Large", "BUTCHER BLOCK", 75)
        90  # Both have 'CUTTING'/'BUTCHER' + 'BOARD'/'BLOCK' keywords
    """
    query_upper = query.upper()
    match_upper = match.upper()

    # Check if both products share keywords from the same category
    for category, keywords in CATEGORY_KEYWORDS.items():
        query_has_keyword = any(kw in query_upper for kw in keywords)
        match_has_keyword = any(kw in match_upper for kw in keywords)

        if query_has_keyword and match_has_keyword:
            # Both products are in the same category - boost confidence
            boosted_score = min(base_score + boost_amount, 100)
            return boosted_score

    # No shared category - return original score
    return base_score


def normalize_product_name(product_name: str) -> str:
    """
    Normalize product name by removing common variant suffixes.

    Strips patterns like:
    - (Noir), (Enfold), (any text in parentheses)
    - -MOF, - Large, - Small, - Set of 3
    - Extra whitespace and dashes

    Args:
        product_name: Original product name

    Returns:
        Normalized product name

    Example:
        >>> normalize_product_name("Upcycled Laptop Sleeve (Enfold)-MOF")
        "UPCYCLED LAPTOP SLEEVE"
        >>> normalize_product_name("Butcher Block - Large")
        "BUTCHER BLOCK"
        >>> normalize_product_name("Candle Holders - Set of 3")
        "CANDLE HOLDERS"
    """
    # Convert to uppercase for consistency
    normalized = product_name.upper()

    # Remove text in parentheses: (Noir), (Enfold), etc.
    normalized = re.sub(r'\([^)]*\)', '', normalized)

    # Remove common variant suffixes
    variant_patterns = [
        r'-\s*MOF',                    # -MOF
        r'-\s*LARGE',                  # - Large
        r'-\s*SMALL',                  # - Small
        r'[-–]\s*SET OF \d+',          # - Set of 3, – Set of 3
        r'-\s*ENFOLD',                 # -ENFOLD (redundant but explicit)
        r'-\s*NOIR',                   # -NOIR (redundant but explicit)
    ]

    for pattern in variant_patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Clean up extra whitespace and dashes
    normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces → single space
    normalized = re.sub(r'\s*-\s*$', '', normalized)  # Trailing dash
    normalized = re.sub(r'^\s*-\s*', '', normalized)  # Leading dash
    normalized = normalized.strip()

    return normalized


class SlideMatchResult:
    """
    Represents the result of matching a product name to a PowerPoint slide.

    Attributes:
        gs_product_name: Product name from Google Sheets
        pptx_product_name: Matched product name from PowerPoint (None if no match)
        match_type: 'exact', 'fuzzy', or 'none'
        confidence: Confidence score (0-100)
        alternatives: List of alternative matches with scores [(name, score), ...]
        match_source: 'manual' or 'automatic' (whether match came from manual override)
        match_method: Description of matching method used (e.g., "Manual override", "Token sort ratio (85%)")
    """

    def __init__(self, gs_product_name: str, pptx_product_name: Optional[str],
                 match_type: str, confidence: int, alternatives: List[Tuple[str, int]] = None,
                 match_source: str = 'automatic', match_method: str = ''):
        self.gs_product_name = gs_product_name
        self.pptx_product_name = pptx_product_name
        self.match_type = match_type
        self.confidence = confidence
        self.alternatives = alternatives or []
        self.match_source = match_source
        self.match_method = match_method

    def is_usable(self, min_confidence: int = 70) -> bool:
        """Check if match is good enough to use automatically."""
        return self.match_type != 'none' and self.confidence >= min_confidence

    def __repr__(self):
        if self.match_source == 'confirmed':
            source_indicator = "[Confirmed]"
        elif self.match_source == 'manual':
            source_indicator = "[Manual]"
        else:
            source_indicator = "[Auto]"
        return f"SlideMatchResult({source_indicator} {self.match_type}, {self.confidence}%, {self.gs_product_name} → {self.pptx_product_name})"


class SlideMatcher:
    """
    Intelligent slide matcher with exact and fuzzy matching capabilities.

    Usage:
        matcher = SlideMatcher(pptx_product_names)
        result = matcher.find_match("Upcycled Laptop Sleeve (Enfold)")
        if result.is_usable():
            print(f"Found match: {result.pptx_product_name}")
    """

    def __init__(self, pptx_product_names: List[str]):
        """
        Initialize matcher with list of product names from PowerPoint.

        Args:
            pptx_product_names: List of product names extracted from PowerPoint slides
        """
        self.pptx_product_names = pptx_product_names

        # Create uppercase mapping for exact matching
        self.pptx_upper_map = {name.upper(): name for name in pptx_product_names}

    def find_match(self, gs_product_name: str, num_alternatives: int = 3, dataset: str = 'demo', template_name: str = '') -> SlideMatchResult:
        """
        Find best matching PowerPoint slide for a Google Sheets product name.

        Args:
            gs_product_name: Product name from Google Sheets
            num_alternatives: Number of alternative matches to return
            dataset: Current dataset ('demo' or 'real') for confirmed match lookup
            template_name: Template name for confirmed match lookup

        Returns:
            SlideMatchResult with match information

        Matching Logic (IMPROVED with Confirmed Match Memory):
            0. Check confirmed matches from Google Sheets FIRST (100% confidence, highest priority)
            1. Check manual matches from JSON (100% confidence, takes precedence)
            2. Normalize product name (strip variants)
            3. Check manual product mappings
            4. Try exact match on normalized name
            5. Multi-scorer fuzzy matching (3 algorithms)
            6. Apply keyword category boosting (+15%)
            7. Return best match with confidence score
        """
        # Step 0: Check confirmed matches from Google Sheets FIRST (highest priority)
        try:
            from .match_memory import get_confirmed_match
            confirmed_match = get_confirmed_match(gs_product_name, dataset, template_name=template_name)

            if confirmed_match:
                # Confirmed match found - return with 100% confidence
                return SlideMatchResult(
                    gs_product_name=gs_product_name,
                    pptx_product_name=confirmed_match['slide_title'],
                    match_type='exact',
                    confidence=100,
                    alternatives=[],
                    match_source='confirmed',
                    match_method=f"Previously confirmed ({confirmed_match['match_type']})"
                )
        except Exception as e:
            # Log error if lookup fails
            print(f"Error looking up confirmed match for '{gs_product_name}': {str(e)}")

        # Step 1: Check manual matches from JSON (legacy system)
        manual_match_data = get_manual_match(gs_product_name, match_category="product")
        if manual_match_data:
            # Manual match found - return with 100% confidence
            return SlideMatchResult(
                gs_product_name=gs_product_name,
                pptx_product_name=manual_match_data['slide_title'],
                match_type='exact',
                confidence=100,
                alternatives=[],
                match_source='manual',
                match_method='Manual override'
            )

        # Step 2: Normalize product name
        normalized_gs_name = normalize_product_name(gs_product_name)

        # Step 3: Check manual product mappings (legacy hardcoded mappings)
        if normalized_gs_name in MANUAL_PRODUCT_MAPPINGS:
            manual_match = MANUAL_PRODUCT_MAPPINGS[normalized_gs_name]
            return SlideMatchResult(
                gs_product_name=gs_product_name,
                pptx_product_name=manual_match,
                match_type='exact',
                confidence=100,
                alternatives=[],
                match_source='automatic',
                match_method='Hardcoded mapping'
            )

        # Step 4: Try exact match on normalized name (case-insensitive)
        if normalized_gs_name in self.pptx_upper_map:
            exact_match = self.pptx_upper_map[normalized_gs_name]
            return SlideMatchResult(
                gs_product_name=gs_product_name,
                pptx_product_name=exact_match,
                match_type='exact',
                confidence=100,
                alternatives=[],
                match_source='automatic',
                match_method='Exact match'
            )

        # Step 5: Multi-scorer fuzzy matching
        # Use normalized name for better matching
        best_match_name, best_match_score, method_used, alternatives = find_best_match_multi_scorer(
            normalized_gs_name,
            self.pptx_product_names,
            limit=num_alternatives
        )

        if best_match_name is None:
            return SlideMatchResult(
                gs_product_name=gs_product_name,
                pptx_product_name=None,
                match_type='none',
                confidence=0,
                alternatives=[],
                match_source='automatic',
                match_method='No match found'
            )

        # Step 6: Apply keyword category boosting
        boosted_score = boost_score_if_same_category(
            normalized_gs_name,
            best_match_name,
            best_match_score
        )

        # Format method description
        method_description = f"{method_used.replace('_', ' ').title()} ({boosted_score}%)"
        if boosted_score > best_match_score:
            method_description += f" [boosted from {best_match_score}%]"

        return SlideMatchResult(
            gs_product_name=gs_product_name,
            pptx_product_name=best_match_name,
            match_type='fuzzy',
            confidence=boosted_score,
            alternatives=alternatives,
            match_source='automatic',
            match_method=method_description
        )

    def batch_match(self, gs_product_names: List[str], dataset: str = 'demo', template_name: str = '') -> List[SlideMatchResult]:
        """
        Match multiple products at once.

        Args:
            gs_product_names: List of product names from Google Sheets
            dataset: Current dataset ('demo' or 'real') for confirmed match lookup
            template_name: Template name for confirmed match lookup

        Returns:
            List of SlideMatchResult objects
        """
        return [self.find_match(name, dataset=dataset, template_name=template_name) for name in gs_product_names]

    def get_match_summary(self, results: List[SlideMatchResult], min_confidence: int = 70) -> Dict:
        """
        Get summary statistics for a batch of match results.

        Args:
            results: List of SlideMatchResult objects
            min_confidence: Minimum confidence threshold for counting usable matches

        Returns:
            Dictionary with summary statistics
        """
        exact_matches = sum(1 for r in results if r.match_type == 'exact')
        fuzzy_matches = sum(1 for r in results if r.match_type == 'fuzzy' and r.confidence >= min_confidence)
        poor_matches = sum(1 for r in results if r.match_type == 'fuzzy' and r.confidence < min_confidence)
        no_matches = sum(1 for r in results if r.match_type == 'none')

        return {
            'total': len(results),
            'exact': exact_matches,
            'fuzzy': fuzzy_matches,
            'poor': poor_matches,
            'none': no_matches,
            'usable': exact_matches + fuzzy_matches,
            'usable_pct': (exact_matches + fuzzy_matches) / len(results) * 100 if results else 0
        }


def build_impact_slide_map(template_path: str) -> Dict[str, Dict]:
    """
    Dynamically discover impact slides in a template and match them to partner names.

    Uses find_all_impact_slides() to discover slides containing "Your Impact",
    then fuzzy-matches each slide's category text against known partner names.

    Args:
        template_path: Path to product slides template

    Returns:
        Dict mapping partner name to impact slide info:
        {
            "Jaggery": {"slide_title": "...", "slide_index": 161},
            "GOEX": {"slide_title": "...", "slide_index": 68},
        }

    Example:
        >>> impact_map = build_impact_slide_map("templates/February All Slides.pptx")
        >>> impact_map["Jaggery"]
        {"slide_title": "Good Felt, ReDenim, and Upcycled Bags - Your Impact", "slide_index": 42}
    """
    # Known partner names to match against
    known_partners = [
        "GOEX", "Gronn", "Homeless Garden Project",
        "Hon's Honey", "Itza Wood", "Jaggery", "Work + Shelter"
    ]

    impact_slides = find_all_impact_slides(template_path)
    if not impact_slides:
        return {}

    result = {}

    for partner in known_partners:
        best_score = 0
        best_slide = None

        for slide_info in impact_slides:
            slide_title = slide_info['slide_title']

            # Extract category part (everything before "Your Impact")
            category_part = slide_title.lower()
            category_part = category_part.replace(" - your impact", "").replace(" \u2013 your impact", "").replace(" \u2014 your impact", "").replace("your impact", "").strip()

            # Fuzzy match partner name against category text
            scores = [
                fuzz.token_sort_ratio(partner.lower(), category_part),
                fuzz.token_set_ratio(partner.lower(), category_part),
                fuzz.partial_ratio(partner.lower(), category_part)
            ]
            max_score = max(scores)

            if max_score > best_score:
                best_score = max_score
                best_slide = slide_info

        # Only include if confidence is reasonable (50%+)
        if best_slide and best_score >= 50:
            result[partner] = {
                'slide_title': best_slide['slide_title'],
                'slide_index': best_slide['slide_index']
            }

    return result


# Confidence threshold constants
CONFIDENCE_EXCELLENT = 90  # Green: Auto-use with high confidence
CONFIDENCE_GOOD = 70       # Yellow: Suggest, ask for confirmation
CONFIDENCE_POOR = 50       # Red: Show but warn user


def format_match_for_display(result: SlideMatchResult) -> str:
    """
    Format a match result for display to user.

    Returns:
        Human-readable string describing the match
    """
    if result.match_type == 'exact':
        return f"✓ Exact match: {result.pptx_product_name}"
    elif result.match_type == 'fuzzy':
        if result.confidence >= CONFIDENCE_EXCELLENT:
            icon = "✓"
            quality = "Excellent"
        elif result.confidence >= CONFIDENCE_GOOD:
            icon = "~"
            quality = "Good"
        else:
            icon = "?"
            quality = "Uncertain"

        return f"{icon} {quality} match ({result.confidence}%): {result.pptx_product_name}"
    else:
        return f"✗ No good match found (best guess: {result.pptx_product_name}, {result.confidence}%)"


# ============================================================
# IMPACT SLIDE MATCHING (PHASE 2.5, DAY 3)
# ============================================================

def extract_partners_and_categories(proposal_products: List[Dict]) -> List[Dict]:
    """
    Extract unique partner-category combinations from proposal products.

    Args:
        proposal_products: List of proposal products with product_data

    Returns:
        List of dicts: [{"partner": "Partner X", "product_category": "Hand Stitched Bags"}]

    Example:
        >>> products = [
        ...     {"product_data": {"Partner": "Partner X", "Product Name": "Jaggery (Noir)"}},
        ...     {"product_data": {"Partner": "Partner X", "Product Name": "Jaggery - Large"}},
        ...     {"product_data": {"Partner": "Partner Y", "Product Name": "Candle Holders"}}
        ... ]
        >>> extract_partners_and_categories(products)
        [
            {"partner": "Partner X", "product_category": "jaggery"},
            {"partner": "Partner Y", "product_category": "candle holders"}
        ]
    """
    unique_combos = set()
    results = []

    for product in proposal_products:
        partner = product['product_data']['Partner']
        product_name = product['product_data']['Product/Service']

        # Normalize product name (strip variants)
        normalized_category = normalize_product_name(product_name)

        combo_key = (partner, normalized_category)
        if combo_key not in unique_combos:
            unique_combos.add(combo_key)
            results.append({
                "partner": partner,
                "product_category": normalized_category,
                "original_product_name": product_name
            })

    return results


def match_impact_slides(
    partners_and_categories: List[Dict],
    template_path: str,
    manual_matches: Dict
) -> List[Dict]:
    """
    Match impact slides for each partner in the proposal.

    Matching Logic:
    1. Check manual matches first (partner_impact_matches section)
    2. If no manual match, search for slides matching pattern: "{category} - Your Impact"
    3. Use fuzzy matching with 75% confidence threshold
    4. Return list of matched impact slides

    Args:
        partners_and_categories: List from extract_partners_and_categories()
            [{"partner": "Partner X", "product_category": "hand stitched bags"}]
        template_path: Path to PowerPoint template
        manual_matches: Dict from load_manual_matches()

    Returns:
        List of matched impact slides:
        [
            {
                "partner": "Partner X",
                "product_category": "hand stitched bags",
                "slide_index": 156,
                "slide_title": "Hand Stitched Bags - Your Impact",
                "confidence": 0.92,
                "match_type": "automatic",  # or "manual"
                "match_method": "Token sort ratio (92%)"  # or "Manual override"
            }
        ]

    Example:
        >>> partners = [{"partner": "Partner X", "product_category": "hand stitched bags"}]
        >>> matches = match_impact_slides(partners, "template.pptx", {})
        >>> matches[0]['slide_title']
        'Hand Stitched Bags - Your Impact'
    """
    results = []

    # Load all slides from template
    try:
        prs = Presentation(template_path)
        all_slides = [(i, slide) for i, slide in enumerate(prs.slides)]
    except Exception as e:
        print(f"Error loading PowerPoint template: {e}")
        return results

    for entry in partners_and_categories:
        partner = entry['partner']
        category = entry['product_category']

        # Check manual matches first
        # Note: normalize_for_storage() converts to lowercase for storage keys
        from .match_manager import normalize_for_storage as normalize_key
        manual_key = normalize_key(f"{partner}_{category}")
        manual_match = manual_matches.get('partner_impact_matches', {}).get(manual_key)

        if manual_match:
            results.append({
                "partner": partner,
                "product_category": category,
                "slide_index": manual_match['slide_index'],
                "slide_title": manual_match['slide_title'],
                "confidence": 1.0,
                "match_type": "manual",
                "match_method": "Manual override"
            })
            continue

        # Run fuzzy matching for impact slides
        # Search pattern: "{category} - Your Impact" or "{category} - your impact"
        search_pattern = f"{category} - Your Impact"
        best_match = None
        best_score = 0

        for slide_idx, slide in all_slides:
            if not slide.shapes.title:
                continue

            slide_title = slide.shapes.title.text.strip()

            # Try multiple fuzzy matching methods
            scores = [
                fuzz.token_sort_ratio(search_pattern.lower(), slide_title.lower()),
                fuzz.token_set_ratio(search_pattern.lower(), slide_title.lower()),
                fuzz.partial_ratio(search_pattern.lower(), slide_title.lower())
            ]

            max_score = max(scores) / 100.0

            if max_score > best_score:
                best_score = max_score
                best_match = {
                    "partner": partner,
                    "product_category": category,
                    "slide_index": slide_idx,
                    "slide_title": slide_title,
                    "confidence": best_score,
                    "match_type": "automatic",
                    "match_method": f"Token fuzzy match ({int(best_score * 100)}%)"
                }

        # Only add if confidence is above threshold (75%)
        if best_match and best_score >= 0.75:
            results.append(best_match)

    return results


def extract_unique_partners(proposal_products: List[Dict]) -> List[str]:
    """
    Extract unique partners from proposal products.

    Args:
        proposal_products: List of proposal products with product_data

    Returns:
        List of unique partner names (sorted alphabetically)

    Example:
        >>> products = [
        ...     {"product_data": {"Partner": "Partner X"}},
        ...     {"product_data": {"Partner": "Partner X"}},
        ...     {"product_data": {"Partner": "Partner Y"}}
        ... ]
        >>> extract_unique_partners(products)
        ['Partner X', 'Partner Y']
    """
    partners = set()
    for product in proposal_products:
        partner = product['product_data'].get('Partner', '')
        if partner:
            partners.add(partner)

    return sorted(list(partners))


def find_all_impact_slides(template_path: str) -> List[Dict]:
    """
    Find all slides in the template with text matching "* - Your Impact".

    Searches ALL text in slides (including text boxes), not just title placeholder,
    since impact slides may have titles in text boxes rather than title placeholders.

    Args:
        template_path: Path to PowerPoint template

    Returns:
        List of impact slide info:
        [
            {
                "slide_index": 156,
                "slide_title": "Hand Stitched Bags – Your Impact"
            },
            ...
        ]

    Example:
        >>> slides = find_all_impact_slides("template.pptx")
        >>> slides[0]['slide_title']
        'Hand Stitched Bags – Your Impact'
    """
    impact_slides = []

    try:
        prs = Presentation(template_path)

        for slide_idx, slide in enumerate(prs.slides):
            # Search ALL text in slide (not just title placeholder)
            for shape in slide.shapes:
                if hasattr(shape, 'text') and shape.text:
                    text = shape.text.strip()

                    # Check if text contains "Your Impact" (case-insensitive)
                    # Handles both "- Your Impact" and "— Your Impact" (em dash)
                    if "your impact" in text.lower():
                        impact_slides.append({
                            "slide_index": slide_idx,
                            "slide_title": text
                        })
                        break  # Only add each slide once

    except Exception as e:
        print(f"Error loading PowerPoint template: {e}")

    # Sort alphabetically by title
    impact_slides.sort(key=lambda x: x['slide_title'])

    return impact_slides


def match_impact_slides_by_partner(
    partners: List[str],
    template_path: str,
    manual_matches: Dict
) -> Dict[str, Dict]:
    """
    Match impact slides for each partner using fuzzy matching and manual overrides.

    Returns suggested matches but does NOT auto-confirm. User must manually select.

    Args:
        partners: List of unique partner names
        template_path: Path to PowerPoint template
        manual_matches: Dict from load_manual_matches() with 'partner_impact_matches' section

    Returns:
        Dict mapping partner to suggested match:
        {
            "Partner X": {
                "suggested_slide_index": 156,
                "suggested_slide_title": "Hand Stitched Bags - Your Impact",
                "confidence": 0.85,
                "match_source": "manual" or "fuzzy" or "none"
            }
        }

    Example:
        >>> partners = ["Partner X", "Partner Y"]
        >>> matches = match_impact_slides_by_partner(partners, "template.pptx", {})
        >>> matches["Partner X"]["suggested_slide_title"]
        'Hand Stitched Bags - Your Impact'
    """
    results = {}

    # Get all impact slides
    all_impact_slides = find_all_impact_slides(template_path)

    if not all_impact_slides:
        return results

    for partner in partners:
        # Check manual matches first
        from .match_manager import normalize_for_storage as normalize_key
        manual_key = normalize_key(partner)
        manual_match = manual_matches.get('partner_impact_matches', {}).get(manual_key)

        if manual_match:
            results[partner] = {
                "suggested_slide_index": manual_match['slide_index'],
                "suggested_slide_title": manual_match['slide_title'],
                "confidence": 1.0,
                "match_source": "manual"
            }
            continue

        # Run fuzzy matching against all impact slide titles
        best_match = None
        best_score = 0

        for impact_slide in all_impact_slides:
            slide_title = impact_slide['slide_title']

            # Extract the category part (everything before "Your Impact")
            # Handle both regular dash and em dash
            category_part = slide_title.lower()
            category_part = category_part.replace(" - your impact", "").replace(" — your impact", "").replace("your impact", "").strip()

            # Try multiple fuzzy matching methods between partner and category
            scores = [
                fuzz.token_sort_ratio(partner.lower(), category_part),
                fuzz.token_set_ratio(partner.lower(), category_part),
                fuzz.partial_ratio(partner.lower(), category_part)
            ]

            max_score = max(scores) / 100.0

            if max_score > best_score:
                best_score = max_score
                best_match = {
                    "suggested_slide_index": impact_slide['slide_index'],
                    "suggested_slide_title": slide_title,
                    "confidence": best_score,
                    "match_source": "fuzzy"
                }

        # Add best match even if confidence is low (user will manually select)
        if best_match:
            results[partner] = best_match
        else:
            # No match found - user must select manually from dropdown
            results[partner] = {
                "suggested_slide_index": None,
                "suggested_slide_title": None,
                "confidence": 0.0,
                "match_source": "none"
            }

    return results
