"""
main.py

FastAPI app wiring: normalize -> classify -> enrich -> redact -> store.

Routes are sync `def` (not `async def`) -- sklearn inference is blocking CPU
work; Starlette runs sync handlers in its threadpool automatically, which is
what you want here rather than stalling the event loop.
"""

import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import config, deps, emailer, store
from api.reasons import enrich
from api.redact import redact
from api.schemas import (
    Advice,
    CheckRequest,
    CheckResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    ObfuscationDetail,
    Reason,
    ReportRequest,
    ReportResponse,
    ShadowConfusion,
    ShadowSummaryResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    clf = deps.load_classifier()
    if not deps.normalizer_loaded():
        raise RuntimeError(
            "normalize.py failed to import inside predict.py -- the model would be "
            "scoring UNNORMALIZED text, which is invalid (the model was trained on "
            "normalized text). Refusing to start. Check that src/ is on sys.path "
            "(see api/paths.py) and that src/normalize.py has no import errors."
        )
    app.state.classifier = clf
    yield


app = FastAPI(title="SafeMoMo API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _new_id(prefix: str) -> str:
    return "{}_{}".format(prefix, uuid.uuid4().hex[:16])


@app.get("/api/health", response_model=HealthResponse)
def health():
    clf = deps.get_classifier() if deps._classifier is not None else None
    return HealthResponse(
        status="ok",
        model_loaded=clf is not None,
        normalizer_loaded=deps.normalizer_loaded(),
        t_low=getattr(clf, "T_LOW", None) if clf else None,
        t_high=getattr(clf, "T_HIGH", None) if clf else None,
        escalation_enabled=config.ENABLE_ESCALATION,
        schema_version=config.SCHEMA_VERSION,
    )


@app.post("/api/check", response_model=CheckResponse)
def check_message(req: CheckRequest):
    clf = deps.get_classifier()

    model_result = clf.classify(req.message, category=req.category or "unknown")

    enriched = enrich(
        normalized_text=req.message,
        model_result=model_result,
        category=req.category or "unknown",
        high_severity=getattr(clf, "HIGH_SEVERITY", None),
        enable_escalation=config.ENABLE_ESCALATION,
    )

    redacted_text, redaction_counts = redact(req.message)
    consent = bool(req.consent_to_log)

    check_id = _new_id("chk")
    checked_at = datetime.now(timezone.utc).isoformat()

    record = {
        "schema_version": config.SCHEMA_VERSION,
        "check_id": check_id,
        "ts": checked_at,
        "model_band": model_result["band"],
        "displayed_band": enriched["band"],
        "band_source": enriched["band_source"],
        "scam_probability": model_result["scam_probability"],
        "obfuscation_suspected": model_result["obfuscation_suspected"],
        "category_input": req.category or "unknown",
        "reason_ids": [r["id"] for r in enriched["reasons"]],
        "message_length": len(req.message),
        "consent": consent,
        "redacted_text": redacted_text if consent else None,
        "redaction_counts": redaction_counts if consent else None,
        "redacted_sha256": hashlib.sha256(redacted_text.encode("utf-8")).hexdigest() if consent else None,
    }
    store.append_check(record)

    return CheckResponse(
        check_id=check_id,
        checked_at=checked_at,
        band=enriched["band"],
        model_band=enriched["model_band"],
        band_source=enriched["band_source"],
        scam_probability=model_result["scam_probability"],
        obfuscation_suspected=model_result["obfuscation_suspected"],
        obfuscation_detail=ObfuscationDetail(
            had_confusable=bool(model_result.get("had_confusable", False)),
            had_invisible_char=bool(model_result.get("had_invisible_char", False)),
        ),
        reasons=[Reason(**r) for r in enriched["reasons"]],
        advice=Advice(**enriched["advice"]),
        model_reasons=model_result.get("reasons", []),
        advisory_only=True,
        logged=True,
        redacted_preview=redacted_text if consent else None,
    )


_LABEL_FOR = {
    "safe": {"helpful": "legitimate", "not_helpful": "scam", "report_scam": "scam"},
    "suspicious": {"helpful": None, "not_helpful": None, "report_scam": "scam"},
}


@app.post("/api/feedback", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest):
    check_record = store.find_check(req.check_id)
    if check_record is None:
        raise HTTPException(status_code=404, detail="unknown check_id")

    model_band = check_record["displayed_band"]
    user_label = _LABEL_FOR.get(model_band, {}).get(req.verdict)
    model_implied_label = "legitimate" if model_band == "safe" else None

    agreement = None
    if user_label is not None and model_implied_label is not None:
        agreement = user_label == model_implied_label

    note_redacted = None
    if req.note:
        note_redacted, _ = redact(req.note)

    feedback_id = _new_id("fb")
    record = {
        "schema_version": config.SCHEMA_VERSION,
        "feedback_id": feedback_id,
        "check_id": req.check_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": req.verdict,
        "user_label": user_label,
        "model_band": model_band,
        "model_implied_label": model_implied_label,
        "agreement": agreement,
        "note_redacted": note_redacted,
    }
    store.append_feedback(record)

    return FeedbackResponse(
        recorded=True,
        feedback_id=feedback_id,
        user_label=user_label,
        agreement=agreement,
        message="Thanks — recorded. This helps the pilot.",
    )


@app.post("/api/report", response_model=ReportResponse)
def submit_report(req: ReportRequest, background: BackgroundTasks):
    message_redacted, _ = redact(req.message)

    report_id = _new_id("rpt")
    record = {
        "schema_version": config.SCHEMA_VERSION,
        "report_id": report_id,
        "check_id": req.check_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "message_redacted": message_redacted,
        "phone": req.phone,
        "email": req.email,
    }
    store.append_report(record)

    # Queue the acknowledgment email AFTER the report is safely persisted;
    # a failed email never fails (or slows) the report itself.
    ack_email_queued = False
    if req.email and emailer.smtp_configured():
        background.add_task(emailer.send_report_ack, req.email, report_id)
        ack_email_queued = True

    return ReportResponse(
        recorded=True,
        report_id=report_id,
        message="Thanks — your report has been received. It has been seen and will be considered by the team.",
        ack_email_queued=ack_email_queued,
    )


@app.get("/api/shadow/summary", response_model=ShadowSummaryResponse)
def shadow_summary():
    s = store.summary()
    confusion = ShadowConfusion(**s["confusion"]) if s["confusion"] else None
    return ShadowSummaryResponse(
        checks_total=s["checks_total"],
        by_band=s["by_band"],
        consented=s["consented"],
        feedback_total=s["feedback_total"],
        confusion=confusion,
        precision=s["precision"],
        recall=s["recall"],
        note=s["note"],
    )


# Production: serve the built frontend from the same service (single origin,
# no CORS needed). Mounted last so every /api route above wins; html=True
# makes / serve index.html. In dev the Vite server runs instead and this
# mount simply doesn't happen (web/dist absent unless built).
_dist = Path(config.WEB_DIST)
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
