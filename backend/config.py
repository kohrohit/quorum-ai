"""Configuration for Quorum AI."""

import os
from dotenv import load_dotenv

load_dotenv()

# API keys for each provider
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Available models catalog
AVAILABLE_MODELS = [
    {"id": "openai/gpt-4o", "provider": "openai", "name": "GPT-4o"},
    {"id": "openai/gpt-4o-mini", "provider": "openai", "name": "GPT-4o Mini"},
    {"id": "openai/gpt-4.1", "provider": "openai", "name": "GPT-4.1"},
    {"id": "openai/gpt-4.1-mini", "provider": "openai", "name": "GPT-4.1 Mini"},
    {"id": "openai/o3-mini", "provider": "openai", "name": "o3-mini"},
    {"id": "google/gemini-2.5-pro", "provider": "google", "name": "Gemini 2.5 Pro"},
    {"id": "google/gemini-2.5-flash", "provider": "google", "name": "Gemini 2.5 Flash"},
    {"id": "google/gemini-2.0-flash", "provider": "google", "name": "Gemini 2.0 Flash"},
    {"id": "anthropic/claude-sonnet-4-5-20250514", "provider": "anthropic", "name": "Claude Sonnet 4.5"},
    {"id": "anthropic/claude-haiku-3-5-20241022", "provider": "anthropic", "name": "Claude Haiku 3.5"},
]

# Default council members
COUNCIL_MODELS = [
    "openai/gpt-4o",
    "google/gemini-2.5-pro",
    "anthropic/claude-sonnet-4-5-20250514",
]

# Default chairman
CHAIRMAN_MODEL = "google/gemini-2.5-pro"

# Default expert roles (empty = no role)
DEFAULT_ROLES = {}

# Default consensus settings
DEFAULT_CONSENSUS_CONFIG = {
    "max_rounds": 5,
    "unanimous_rounds": 3,
}

# Provider API endpoints
PROVIDER_CONFIG = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_var": "OPENAI_API_KEY",
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "key_var": "GOOGLE_API_KEY",
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "key_var": "ANTHROPIC_API_KEY",
    },
}

# Approximate cost per 1M tokens (input/output) for dashboard
MODEL_COSTS = {
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4.1": {"input": 2.00, "output": 8.00},
    "openai/gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "openai/o3-mini": {"input": 1.10, "output": 4.40},
    "google/gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "google/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "google/gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "anthropic/claude-sonnet-4-5-20250514": {"input": 3.00, "output": 15.00},
    "anthropic/claude-haiku-3-5-20241022": {"input": 0.80, "output": 4.00},
}

# Data directory
DATA_DIR = "data/conversations"
SETTINGS_FILE = "data/settings.json"
