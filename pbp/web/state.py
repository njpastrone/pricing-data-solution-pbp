"""
The working order of each staff session, kept in process memory.

Refresh, second tab, closed laptop: the order is still there. A deploy or
restart loses unsaved work, exactly like the Streamlit app today; staff save
named orders to the saved_orders sheet as before.
"""
# ponytail: in-memory per process; autosave "working" rows to the saved_orders sheet if deploy-survival is ever needed

import threading

from pbp.services import order as order_service
from pbp.services import proposal as proposal_service

_lock = threading.Lock()
_orders = {}   # session id -> order dict
_proposals = {}  # session id -> proposal dict
_photos = {}   # session id -> {product_name: [{"bytes", "filename"}]}
_meta = {}     # session id -> {"loaded_order_id", "loaded_order_name", "proposal_products", "flash"}


def order(sid):
    with _lock:
        if sid not in _orders:
            _orders[sid] = order_service.new_order()
        return _orders[sid]


def replace_order(sid, new_order, order_id=None, name=None):
    with _lock:
        _orders[sid] = order_service.normalize(new_order)
        _photos[sid] = {}
        meta(sid).update(loaded_order_id=order_id, loaded_order_name=name)


def clear_order(sid):
    replace_order(sid, order_service.new_order())


def proposal(sid):
    with _lock:
        if sid not in _proposals:
            _proposals[sid] = proposal_service.new_proposal()
        return _proposals[sid]


def replace_proposal(sid, new_proposal, proposal_id=None, name=None):
    with _lock:
        _proposals[sid] = proposal_service.normalize(new_proposal)
        meta(sid).update(loaded_proposal_id=proposal_id, loaded_proposal_name=name, pptx={})


def photos(sid):
    with _lock:
        return _photos.setdefault(sid, {})


def meta(sid):
    return _meta.setdefault(sid, {"loaded_order_id": None, "loaded_order_name": None, "proposal_products": [], "flash": [],
                                  "loaded_proposal_id": None, "loaded_proposal_name": None, "catalog_filters": {}, "pptx": {}})


def flash(sid, message, kind="success"):
    meta(sid)["flash"].append((kind, message))


def pop_flash(sid):
    messages = meta(sid)["flash"]
    meta(sid)["flash"] = []
    return messages
