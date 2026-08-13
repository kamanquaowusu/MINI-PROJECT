"""
config.py

Plain os.environ settings -- no pydantic-settings dependency needed for this
few knobs.
"""

import os

from api.paths import PROJECT_ROOT


def _bool(name, default):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() not in ("0", "false", "no", "off", "")


MODEL_PATH = os.environ.get(
    "SAFEMOMO_MODEL_PATH", str(PROJECT_ROOT / "models" / "triage_model.joblib")
)
SHADOW_DIR = os.environ.get(
    "SAFEMOMO_SHADOW_DIR", str(PROJECT_ROOT / "data" / "shadow")
)
ENABLE_ESCALATION = _bool("SAFEMOMO_ENABLE_ESCALATION", True)
MAX_MESSAGE_CHARS = int(os.environ.get("SAFEMOMO_MAX_MESSAGE_CHARS", "1600"))
MAX_STORED_CHARS = int(os.environ.get("SAFEMOMO_MAX_STORED_CHARS", "1000"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "SAFEMOMO_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

SCHEMA_VERSION = 1
