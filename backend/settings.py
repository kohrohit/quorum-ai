"""Settings persistence for council configuration."""

import json
import os
from pathlib import Path
from typing import Dict, Any
from .config import (
    COUNCIL_MODELS, CHAIRMAN_MODEL, SETTINGS_FILE,
    DEFAULT_ROLES, DEFAULT_CONSENSUS_CONFIG,
)

_DEFAULT_SETTINGS = {
    "council_models": COUNCIL_MODELS,
    "chairman_model": CHAIRMAN_MODEL,
    "roles": DEFAULT_ROLES,
    "consensus": DEFAULT_CONSENSUS_CONFIG,
}


def load_settings() -> Dict[str, Any]:
    """Load settings from file, or return defaults."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
        # Merge with defaults for any missing keys
        merged = {**_DEFAULT_SETTINGS, **saved}
        return merged
    return dict(_DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]):
    """Save settings to file."""
    Path(os.path.dirname(SETTINGS_FILE)).mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def update_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update specific settings fields and save."""
    current = load_settings()
    current.update(updates)
    save_settings(current)
    return current
