"""
emailer.py

Acknowledgment email for scam reports.

Transport priority:
  1. Brevo HTTP API (HTTPS/443) -- REQUIRED on Render's free tier, which
     blocks outbound SMTP ports 25/465/587 entirely. An SMTP send there
     doesn't error quickly, it hangs until timeout, so the only workable
     transport on a free instance is an HTTP API.
  2. SMTP STARTTLS -- local development, or hosts that allow SMTP.

Uses urllib from the stdlib rather than requests/the Brevo SDK: this
service pins its dependencies to the exact versions the model was trained
with, and an email helper is not worth widening that surface.

send_report_ack() returns True ONLY if the provider accepted the message,
and never raises -- the report is already persisted before it is called,
so a mail failure must never turn into a failed report. The caller
surfaces the real result, so the UI never claims an email is coming when
it isn't.
"""

import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from api import config

logger = logging.getLogger("safemomo.emailer")

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
SEND_TIMEOUT_SECONDS = 10

ACK_SUBJECT = "SafeMoMo — your scam report has been received"
ACK_BODY = """Hello,

Thank you for reporting a suspicious message to SafeMoMo.

Your report (reference: {report_id}) has been received and seen, and it
will be considered by the team. If a follow-up is needed, we will contact
you on the details you provided.

A few reminders while you wait:
  - Never share your PIN or OTP with anyone.
  - Don't call numbers or tap links from suspicious messages.
  - You can also report scams to your network provider on 100.

— The SafeMoMo pilot team

(This is an automated acknowledgment; replies to this address are not
monitored.)
"""


def brevo_configured() -> bool:
    return bool(config.BREVO_API_KEY and config.FROM_EMAIL)


def smtp_configured() -> bool:
    return bool(config.SMTP_USER and config.SMTP_PASSWORD)


def email_configured() -> bool:
    """True if ANY transport can currently send."""
    return brevo_configured() or smtp_configured()


def _send_via_brevo(to_email: str, report_id: str) -> bool:
    payload = {
        "sender": {"name": config.FROM_NAME, "email": config.FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": ACK_SUBJECT,
        "textContent": ACK_BODY.format(report_id=report_id),
    }
    request = urllib.request.Request(
        BREVO_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": config.BREVO_API_KEY,
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=SEND_TIMEOUT_SECONDS) as response:
            # Brevo returns 201 Created with a messageId on success.
            if 200 <= response.status < 300:
                logger.info("Brevo accepted ack email for %s", report_id)
                return True
            logger.error("Brevo returned HTTP %s for %s", response.status, report_id)
            return False
    except urllib.error.HTTPError as exc:
        # Body carries Brevo's reason (unverified sender, bad key, quota).
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        logger.error("Brevo HTTPError %s for %s: %s", exc.code, report_id, detail)
        return False
    except Exception:
        logger.exception("Brevo request failed for %s", report_id)
        return False


def _send_via_smtp(to_email: str, report_id: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = ACK_SUBJECT
    msg["From"] = "{} <{}>".format(config.FROM_NAME, config.FROM_EMAIL or config.SMTP_USER)
    msg["To"] = to_email
    msg.set_content(ACK_BODY.format(report_id=report_id))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=SEND_TIMEOUT_SECONDS) as smtp:
            smtp.starttls()
            smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("SMTP sent ack email for %s", report_id)
        return True
    except Exception:
        logger.exception("SMTP send failed for %s", report_id)
        return False


def send_report_ack(to_email: str, report_id: str) -> bool:
    """Send the acknowledgment email. True only if a provider accepted it."""
    if brevo_configured():
        return _send_via_brevo(to_email, report_id)
    if smtp_configured():
        return _send_via_smtp(to_email, report_id)
    logger.info("No email transport configured; skipping ack for %s", report_id)
    return False
