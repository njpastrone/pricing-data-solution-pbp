"""
Product catalog (the master_pricing spreadsheet) for the web app.

Loads the Data, Metadata and Partner-Specific Info tabs into DataFrames and
keeps them for five minutes, process-wide, so every staff request shares one
read (Google allows about 60 reads per minute for the whole service account).
"""

import threading
import time

import pandas as pd

from pbp.core.helpers import extract_partner_contacts
from pbp.sheets import gateway

DATASETS = {
    "demo": {"name": "Demo Data (master_pricing_template_10_14)", "spreadsheet_id": "1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs"},
    "real": {"name": "Real Pricing Data (master_pricing)", "spreadsheet_id": "1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms"},
}
CACHE_SECONDS = 300

_lock = threading.Lock()
_cache = {}  # dataset -> (loaded_at, (df_template, df_metadata, df_partner_info))


def load_pricing_data(dataset="real", force=False):
    """
    (df_template, df_metadata, df_partner_info) for a dataset, cached for CACHE_SECONDS.

    Data tab: header row 7, data from row 8; Metadata: header row 2;
    Partner-Specific Info: header row 2 (real) or row 3 (demo).
    """
    if dataset not in DATASETS:
        raise KeyError(f"Invalid dataset '{dataset}'. Must be one of {list(DATASETS)}.")
    with _lock:
        cached = _cache.get(dataset)
        if cached and not force and time.time() - cached[0] < CACHE_SECONDS:
            return cached[1]
    frames = _read_pricing_data(dataset)
    with _lock:
        _cache[dataset] = (time.time(), frames)
    return frames


def loaded_at(dataset="real"):
    """Unix time of the cached load, or None."""
    cached = _cache.get(dataset)
    return cached[0] if cached else None


def partner_contacts(dataset="real"):
    """{partner: {poc_name, poc_email, poc_phone}} from the Partner-Specific Info tab."""
    _, _, df_partner_info = load_pricing_data(dataset)
    return extract_partner_contacts(df_partner_info) if not df_partner_info.empty else {}


def find_product(df_template, product_name, partner=None):
    """The catalog row (as a dict) for a product name, matched exactly ignoring case; None if absent."""
    rows = df_template[df_template["Product/Service"].str.lower().str.strip() == str(product_name).lower().strip()]
    if partner is not None:
        rows = rows[rows["Partner"] == partner]
    return rows.iloc[0].to_dict() if not rows.empty else None


def _frame(values, header_index, data_index):
    """DataFrame from raw sheet values, dropping leading empty columns and rows without a Partner."""
    if len(values) <= header_index:
        return pd.DataFrame()
    raw_headers = values[header_index]
    first_col = next((i for i, h in enumerate(raw_headers) if h.strip()), 0)
    headers = [h.strip() if h else f"Unnamed_{i}" for i, h in enumerate(raw_headers[first_col:])]
    rows = [row[first_col:] for row in values[data_index:]]
    df = pd.DataFrame(rows, columns=headers)
    if "Partner" in df.columns:
        df = df[df["Partner"].str.strip() != ""]
    return df


def _read_pricing_data(dataset):
    spreadsheet = gateway.retry_on_quota(lambda: gateway.connect().open_by_key(DATASETS[dataset]["spreadsheet_id"]))
    data = gateway.retry_on_quota(lambda: spreadsheet.worksheet("Data").get_all_values())
    metadata = gateway.retry_on_quota(lambda: spreadsheet.worksheet("Metadata").get_all_values())
    partners = gateway.retry_on_quota(lambda: spreadsheet.worksheet("Partner-Specific Info").get_all_values())
    partner_header = 1 if dataset == "real" else 2
    return (
        _frame(data, 6, 7),
        _frame(metadata, 1, 2),
        _frame(partners, partner_header, partner_header + 1),
    )
