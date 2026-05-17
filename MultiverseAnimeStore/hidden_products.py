import json
import os
import threading

_HIDDEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hidden_products.json')
_lock = threading.Lock()


def _read_hidden():
    if not os.path.exists(_HIDDEN_FILE):
        return set()
    try:
        with open(_HIDDEN_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
            return set(raw) if isinstance(raw, list) else set()
    except (json.JSONDecodeError, OSError):
        return set()


def _write_hidden(hidden_set):
    os.makedirs(os.path.dirname(_HIDDEN_FILE), exist_ok=True)
    with open(_HIDDEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted(hidden_set), f, indent=2)


def get_hidden_product_ids():
    with _lock:
        return _read_hidden()


def is_product_hidden(prod_id):
    return str(prod_id) in get_hidden_product_ids()


def toggle_product_hidden(prod_id):
    prod_id = str(prod_id)
    with _lock:
        hidden = _read_hidden()
        if prod_id in hidden:
            hidden.discard(prod_id)
            action = 'shown'
        else:
            hidden.add(prod_id)
            action = 'hidden'
        _write_hidden(hidden)
        return action
