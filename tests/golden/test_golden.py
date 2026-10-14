"""
Golden parity tests: recompute every snapshot in tests/golden/snapshots/ from
its stored inputs and compare with the stored outputs. See golden.py for how
snapshots are generated (read-only against the live Sheets).

With no snapshots present only the self-check below runs.
"""

import glob
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import golden  # noqa: E402

ORDER_SNAPSHOTS = sorted(glob.glob(os.path.join(golden.SNAPSHOT_DIR, "orders", "*.json")))
PROPOSAL_SNAPSHOTS = sorted(glob.glob(os.path.join(golden.SNAPSHOT_DIR, "proposals", "*.json")))


def _load(path):
    with open(path) as handle:
        return json.load(handle)


@pytest.mark.parametrize("path", ORDER_SNAPSHOTS, ids=os.path.basename)
def test_order_pricing_unchanged(path):
    snapshot = _load(path)
    assert golden.order_snapshot(snapshot["input"]) == snapshot["expected"]


@pytest.mark.parametrize("path", PROPOSAL_SNAPSHOTS, ids=os.path.basename)
def test_proposal_pricing_unchanged(path):
    snapshot = _load(path)
    assert golden.proposal_pricing_snapshot(snapshot["input"]) == snapshot["expected"]["pricing"]


@pytest.mark.parametrize("path", PROPOSAL_SNAPSHOTS, ids=os.path.basename)
def test_proposal_pptx_unchanged(path):
    snapshot = _load(path)
    dataset = snapshot.get("dataset") or "real"
    assert golden.proposal_pptx_snapshot(snapshot["input"], dataset) == snapshot["expected"]["pptx"]


# ----------------------------------------------------------------------------
# Self-check on a synthetic order and proposal, so the snapshot machinery is
# exercised even before real snapshots are committed.
# ----------------------------------------------------------------------------

SAMPLE_PRODUCT = {
    "Partner": "Test Partner",
    "Product/Service": "Test Product",
    "Pricing Tiers (Y/N)": "N",
    "PBP Cost (No Tiers)": "$25.00",
    "MOQ (Partner)": 50,
    "Country of Origin (Made In)": "USA",
    "Country of Origin (Ships From)": "USA",
}

SAMPLE_ORDER = {
    "order_items": [
        {
            "product_name": "Test Product",
            "product_data": SAMPLE_PRODUCT,
            "quantity": 100,
            "markup_percent": 100,
            "product_subtotal": 2500.0,
            "markup_amount": 2500.0,
            "include_customization": False,
        },
        {"product_name": "Rush fee", "is_custom": True, "quantity": 1,
         "total_per_unit": 50.0, "product_total": 50.0},
    ]
}

SAMPLE_PROPOSAL = {
    "proposal_products": [
        {"product_data": SAMPLE_PRODUCT, "quantity": 100, "markup_percent": 100}
    ],
    "proposal_marketing_rounding": False,
    "proposal_discount_percent": 0.0,
}


def test_order_snapshot_self_check():
    snapshot = golden.order_snapshot(SAMPLE_ORDER)
    line = snapshot["items"][0]
    assert line["unit_price"] == 25.0
    assert line["quote"]["product_cost_with_markup"] == 5000.0
    assert line["moq"] == 50
    assert snapshot["items"][1] == {"product_name": "Rush fee", "quantity": 1, "custom": True}
    assert snapshot == golden.plain(snapshot)  # JSON-stable, so it can be stored and compared


def test_proposal_pricing_snapshot_self_check():
    snapshot = golden.proposal_pricing_snapshot(SAMPLE_PROPOSAL)
    line = snapshot["items"][0]
    assert line["proposal_pricing"]["moq"] == 50
    assert line["proposal_pricing"]["moq_price_per_unit"] == 50.0
    assert line["pbp_msrp"]["pbp_msrp"] == 50.0
