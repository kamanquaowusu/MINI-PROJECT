"""
emailer.py

Acknowledgment email for scam reports. Deliberately dormant until SMTP
credentials are configured (SAFEMOMO_SMTP_USER + SAFEMOMO_SMTP_PASSWORD --
for Gmail this must be an App Password, not the account password).

send_report_ack() runs as a FastAPI background task: it must never raise
into the request path, so every failure is caught and logged. A failed
acknowledgment email must not fail the report itself -- the report is
already persisted by the time this runs.
"""

import logging
import smtplib
from email.message import EmailMessage

from api import config

logger = logging.getLogger("safemomo.emailer")

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


def smtp_configured() -> bool:
    return bool(config.SMTP_USER and config.SMTP_PASSWORD)


def send_report_ack(to_email: str, report_id: str) -> bool:
    """Send the acknowledgment email. Returns True on success, False otherwise."""
    if not smtp_configured():
        logger.info("SMTP not configured; skipping ack email for %s", report_id)
        return False

    msg = EmailMessage()
    msg["Subject"] = ACK_SUBJECT
    msg["From"] = "{} <{}>".format(config.FROM_NAME, config.SMTP_USER)
    msg["To"] = to_email
    msg.set_content(ACK_BODY.format(report_id=report_id))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("Sent report ack for %s", report_id)
        return True
    except Exception:
        logger.exception("Failed to send report ack for %s", report_id)
        return False
