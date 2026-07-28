"""Temporary input persistence for the build/setup phase.

Caches the last-entered input values to a local JSON file so they survive a
browser refresh (Streamlit normally resets to defaults on a hard refresh,
since a refresh starts a brand-new session). Remove this module and its
two call sites in user_inputs.py once inputs stabilise and this is no
longer needed.
"""

import json
import os

_CACHE_PATH = os.path.join(os.path.dirname(__file__), ".dev_input_cache.json")


def load():
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save(data):
    try:
        with open(_CACHE_PATH, "w") as f:
            json.dump(data, f)
    except OSError:
        pass
