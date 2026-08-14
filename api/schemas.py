"""
schemas.py

Pydantic v2 request/response models. Python 3.8-compatible typing only:
typing.Optional / typing.List / typing.Dict / typing.Literal -- no `str | None`,
no bare generic subscripting in annotations (Pydantic evaluates these at
runtime and 3.8 doesn't support PEP 604/585 there).
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1600)
    category: Optional[str] = "unknown"
    consent_to_log: bool = False


class Reason(BaseModel):
    id: str
    kind: Literal["red_flag", "clear"]
    text: str


class Advice(BaseModel):
    title: str
    text: str


class ObfuscationDetail(BaseModel):
    had_confusable: bool
    had_invisible_char: bool


class CheckResponse(BaseModel):
    check_id: str
    checked_at: str
    band: Literal["safe", "suspicious"]
    model_band: Literal["safe", "suspicious"]
    band_source: Literal["model", "heuristic_escalation"]
    scam_probability: float
    obfuscation_suspected: bool
    obfuscation_detail: ObfuscationDetail
    reasons: List[Reason]
    advice: Advice
    model_reasons: List[str]
    advisory_only: bool = True
    logged: bool
    redacted_preview: Optional[str] = None


class FeedbackRequest(BaseModel):
    check_id: str
    verdict: Literal["helpful", "not_helpful", "report_scam"]
    note: Optional[str] = None


class FeedbackResponse(BaseModel):
    recorded: bool
    feedback_id: str
    user_label: Optional[Literal["scam", "legitimate"]]
    agreement: Optional[bool]
    message: str


class ReportRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1600)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=254)
    check_id: Optional[str] = None


class ReportResponse(BaseModel):
    recorded: bool
    report_id: str
    message: str
    ack_email_queued: bool = False


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    normalizer_loaded: bool
    t_low: Optional[float] = None
    t_high: Optional[float] = None
    escalation_enabled: bool
    advisory_only: bool = True
    schema_version: int


class ShadowConfusion(BaseModel):
    tp: int
    fp: int
    tn: int
    fn: int


class ShadowSummaryResponse(BaseModel):
    checks_total: int
    by_band: Dict[str, int]
    consented: int
    feedback_total: int
    confusion: Optional[ShadowConfusion] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    note: str = "Pilot shadow data from user feedback. Not a validated benchmark."
