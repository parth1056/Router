"""Canonical runtime-visible state; never serialize annotation fields."""
import json

KEYS = ("message", "history", "assets", "active_image_id", "last_analysis")

def serialize(state):
    if set(state) != set(KEYS):
        raise ValueError("Unexpected/missing runtime state keys")
    # Order is deliberate: newest request must not be lost behind old history.
    ordered = {k: state[k] for k in ("message", "assets", "active_image_id", "last_analysis", "history")}
    return json.dumps(ordered, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

def supported_asset_exists(state):
    return any(a["kind"] == "image" and a["availability"] == "available"
               and a["support"] == "supported" for a in state["assets"])
