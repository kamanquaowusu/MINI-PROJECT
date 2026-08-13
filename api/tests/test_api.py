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
