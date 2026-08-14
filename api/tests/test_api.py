import json

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFEMOMO_SHADOW_DIR", str(tmp_path / "shadow"))
    # Reload config/store/main so they pick up the env var set above -- these
    # modules read config.SHADOW_DIR at import time via api.config constants.
    import importlib
    import api.config as config_mod
    import api.store as store_mod
    import api.main as main_mod

    importlib.reload(config_mod)
    importlib.reload(store_mod)
    importlib.reload(main_mod)

    from fastapi.testclient import TestClient

    with TestClient(main_mod.app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["normalizer_loaded"] is True
    assert body["model_loaded"] is True


def test_check_without_consent_does_not_persist_text(client, tmp_path):
    r = client.post("/api/check", json={
        "message": "Confirmed. You have received GHS50.00 from KWAME.",
        "consent_to_log": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["redacted_preview"] is None

    shadow_file = tmp_path / "shadow" / "checks.jsonl"
    lines = shadow_file.read_text().strip().splitlines()
    last = json.loads(lines[-1])
    assert last["consent"] is False
    assert last["redacted_text"] is None
    assert last["model_band"] in ("safe", "suspicious")


def test_check_with_consent_persists_redacted_text_only(client, tmp_path):
    r = client.post("/api/check", json={
        "message": "Confirmed. You have received GHS50.00 from KWAME. Call 0244123456.",
        "consent_to_log": True,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["redacted_preview"] is not None
    assert "KWAME" not in body["redacted_preview"]
    assert "0244123456" not in body["redacted_preview"]

    shadow_file = tmp_path / "shadow" / "checks.jsonl"
    last = json.loads(shadow_file.read_text().strip().splitlines()[-1])
    assert last["consent"] is True
    assert "KWAME" not in last["redacted_text"]
    assert "0244123456" not in last["redacted_text"]


def test_feedback_round_trip(client):
    check = client.post("/api/check", json={
        "message": "URGENT verify your PIN now at momo-verify.gh",
        "consent_to_log": False,
    }).json()
    assert check["band"] == "suspicious"

    fb = client.post("/api/feedback", json={
        "check_id": check["check_id"],
        "verdict": "not_helpful",
    })
    assert fb.status_code == 200
    body = fb.json()
    # "suspicious" is inherently ambiguous -- no ground-truth label is implied.
    assert body["user_label"] is None
    assert body["agreement"] is None


def test_feedback_unknown_check_id_404(client):
    r = client.post("/api/feedback", json={"check_id": "does-not-exist", "verdict": "helpful"})
    assert r.status_code == 404


def test_check_message_length_validation(client):
    assert client.post("/api/check", json={"message": "", "consent_to_log": False}).status_code == 422
    assert client.post("/api/check", json={"message": "x" * 2000, "consent_to_log": False}).status_code == 422


def test_shadow_summary_reflects_checks(client):
    client.post("/api/check", json={"message": "hello there", "consent_to_log": False})
    r = client.get("/api/shadow/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["checks_total"] >= 1


def test_report_persists_redacted_message(client, tmp_path):
    r = client.post("/api/report", json={
        "message": "Send your PIN to 0244123456 to claim GHS500",
        "phone": "0501234567",
        "email": "user@example.com",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["recorded"] is True
    assert body["report_id"].startswith("rpt_")

    reports_file = tmp_path / "shadow" / "reports.jsonl"
    last = json.loads(reports_file.read_text().strip().splitlines()[-1])
    # The reported message must be stored redacted; the reporter's own
    # contact details are stored as given (they volunteered them for follow-up).
    assert "0244123456" not in last["message_redacted"]
    assert last["phone"] == "0501234567"
    assert last["email"] == "user@example.com"
    assert last["check_id"] is None


def test_report_optional_fields_default_null(client, tmp_path):
    r = client.post("/api/report", json={"message": "suspicious scam text here"})
    assert r.status_code == 200
    reports_file = tmp_path / "shadow" / "reports.jsonl"
    last = json.loads(reports_file.read_text().strip().splitlines()[-1])
    assert last["phone"] is None
    assert last["email"] is None


def test_report_message_validation(client):
    assert client.post("/api/report", json={"message": ""}).status_code == 422
    assert client.post("/api/report", json={"message": "x" * 2000}).status_code == 422
