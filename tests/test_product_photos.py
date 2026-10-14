"""Regression tests for product photo attachment (Tab 3, section 5)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from types import SimpleNamespace

from pbp.core.helpers import add_product_photos


def _photo(name, size=100):
    return SimpleNamespace(name=name, size=size)


def test_same_upload_on_rerun_attaches_once():
    """Streamlit re-sends the uploader value on every rerun; it must not re-append."""
    uploaded = [_photo("mug.png")]
    photos = []
    for _ in range(5):  # five reruns used to produce five copies
        photos, _ = add_product_photos(photos, uploaded)
    assert len(photos) == 1


def test_distinct_photos_are_all_added():
    photos, skipped = add_product_photos([], [_photo("a.png"), _photo("b.png"), _photo("a.png", size=999)])
    assert [p.name for p in photos] == ["a.png", "b.png", "a.png"]
    assert skipped == 0


def test_cap_of_five_is_enforced():
    uploaded = [_photo(f"{i}.png") for i in range(7)]
    photos, skipped = add_product_photos([], uploaded)
    assert len(photos) == 5
    assert skipped == 2


def test_existing_photos_are_kept():
    existing = [_photo("old.png")]
    photos, _ = add_product_photos(existing, [_photo("new.png")])
    assert [p.name for p in photos] == ["old.png", "new.png"]
