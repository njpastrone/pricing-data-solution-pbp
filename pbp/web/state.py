"""
The working order of each staff session, kept in process memory.

Refresh, second tab, closed laptop: the order is still there. A deploy or
restart loses unsaved work, exactly like the Streamlit app today; staff save
named orders to the saved_orders sheet as before.
"""
# ponytail: in-memory per process; autosave "working" rows to the saved_orders sheet if deploy-survival is ever needed

import threading

from pbp.services import order as order_service

_lock = threading.Lock()
_orders = {}   # session id -> order dict
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


def photos(sid):
    with _lock:
        return _photos.setdefault(sid, {})


def meta(sid):
    return _meta.setdefault(sid, {"loaded_order_id": None, "loaded_order_name": None, "proposal_products": [], "flash": []})


def flash(sid, message, kind="success"):
    meta(sid)["flash"].append((kind, message))


def pop_flash(sid):
    messages = meta(sid)["flash"]
    meta(sid)["flash"] = []
    return messages
