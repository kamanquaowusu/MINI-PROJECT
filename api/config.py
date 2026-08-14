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

# Built frontend, served by FastAPI in production (single-service deploy).
WEB_DIST = os.environ.get("SAFEMOMO_WEB_DIST", str(PROJECT_ROOT / "web" / "dist"))

# Acknowledgment email for scam reports. Two transports, tried in order:
#
#   1. Brevo HTTP API (preferred) -- plain HTTPS on 443. Render's FREE tier
#      blocks outbound SMTP ports 25/465/587, so SMTP simply cannot work
#      there; an HTTP API is the only way to send from a free instance.
#   2. SMTP -- kept for local development and for hosts that permit it
#      (e.g. a paid Render instance).
#
# Both dormant until credentials are supplied.
BREVO_API_KEY = os.environ.get("SAFEMOMO_BREVO_API_KEY", "")

SMTP_HOST = os.environ.get("SAFEMOMO_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SAFEMOMO_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SAFEMOMO_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SAFEMOMO_SMTP_PASSWORD", "")

FROM_NAME = os.environ.get("SAFEMOMO_FROM_NAME", "SafeMoMo")
# Sender address. Must be a verified sender in Brevo. Defaults to SMTP_USER
# so an existing SMTP-only deployment keeps working unchanged.
FROM_EMAIL = os.environ.get("SAFEMOMO_FROM_EMAIL", "") or SMTP_USER

SCHEMA_VERSION = 1
