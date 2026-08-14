from api.reasons import enrich


def safe_result(obfuscation=False):
    return {"band": "safe", "scam_probability": 0.0, "obfuscation_suspected": obfuscation, "reasons": []}


def high_prob_suspicious_result(obfuscation=False):
    return {"band": "suspicious", "scam_probability": 0.99, "obfuscation_suspected": obfuscation, "reasons": []}


def ids(result):
    return {r["id"] for r in result["reasons"]}


def test_pin_block_link_flags():
    text = "your momo wallet will be blocked, verify your pin now at mtn-momo-verify.co"
    result = enrich(text, high_prob_suspicious_result())
    got = ids(result)
    assert "pin_request" in got
    assert "threat_block" in got
    assert ("impersonation" in got) or ("suspicious_link" in got)


def test_prize_send_amount_flags():
    text = "congratulations you have won ghs5,000 in the mtn promo! send ghs20 to claim your prize now"
    result = enrich(text, high_prob_suspicious_result())
    got = ids(result)
    assert "prize_promo" in got
    assert "pay_to_receive" in got


def test_refund_urgency_personal_number():
    text = "your ghs 800.00 was sent to your wallet in error. kindly refund within 10 minutes to 0244123456"
    result = enrich(text, high_prob_suspicious_result())
    got = ids(result)
    assert {"refund_reversal", "urgency", "personal_number"} <= got
    urgency_reason = next(r for r in result["reasons"] if r["id"] == "urgency")
    assert "within 10 minutes" in urgency_reason["text"]


def test_clean_payment_alert_is_clear_and_has_no_pin_request():
    text = "payment received. ghs 120.00 from ama owusu. ref txn-9921-04. balance ghs 340.50."
    result = enrich(text, safe_result())
    assert all(r["kind"] == "clear" for r in result["reasons"])
    assert len(result["reasons"]) >= 2
    assert "no_pin_request" in ids(result)


def test_reasons_never_empty_and_kind_consistent_for_non_safe():
    cases = [
        (high_prob_suspicious_result(), "ok this is a totally boring message with nothing special about it at all"),
        (safe_result(), "hello there just checking in"),
    ]
    for model_result, text in cases:
        result = enrich(text, model_result)
        assert len(result["reasons"]) >= 1
        if result["band"] != "safe":
            assert all(r["kind"] == "red_flag" for r in result["reasons"])
        else:
            assert all(r["kind"] == "clear" for r in result["reasons"])


def test_escalation_raises_safe_to_suspicious_without_touching_model_band():
    text = "here is your link bit.ly/abc123 for details"
    result = enrich(text, safe_result(), enable_escalation=True)
    assert result["band"] == "suspicious"
    assert result["model_band"] == "safe"
    assert result["band_source"] == "heuristic_escalation"


def test_escalation_can_be_disabled():
    text = "here is your link bit.ly/abc123 for details"
    result = enrich(text, safe_result(), enable_escalation=False)
    assert result["band"] == "safe"
    assert result["band_source"] == "model"


def test_escalation_never_touches_already_suspicious():
    text = "here is your link bit.ly/abc123 for details"
    result = enrich(text, high_prob_suspicious_result(), enable_escalation=True)
    assert result["band"] == "suspicious"
    assert result["band_source"] == "model"


def test_allowlisted_telco_links_do_not_escalate():
    # Real MTN / Telecel broadcast links must not push a model-safe message
    # to suspicious: these exact domains/paths are telco-controlled.
    cases = [
        "Special Deal! Enjoy 1.5GB for 7 days at GHc4. Dial *141# or visit myMTN App via https://mymtn.onelink.me/cB5t/MTN4G6",
        "Out of credit? Simply dial *505# or visit https://bit.ly/TelecelPlayGhana to get an airtime loan whenever you need it!",
        "Access Telecel data via *200# or the Telecel Play App - https://telecel.me/TelecelPlayApp",
    ]
    for text in cases:
        result = enrich(text, safe_result(), enable_escalation=True)
        assert result["band"] == "safe", text
        assert result["band_source"] == "model"


def test_reward_marketing_without_payment_demand_does_not_escalate():
    text = "Get rewarded for staying connected! Install the MyMTN App for exclusive data deals and special Just4U offers."
    result = enrich(text, safe_result(), enable_escalation=True)
    assert result["band"] == "safe"


def test_refund_education_without_corroboration_does_not_escalate():
    # Telcos legitimately explain HOW to reverse wrong transactions.
    text = "Dear Customer, do you know you can reverse a wrong Telecel Cash transaction on TERi? Chat via https://telecel.me/TERiWhatsApp"
    result = enrich(text, safe_result(), enable_escalation=True)
    assert result["band"] == "safe"


def test_refund_with_amount_and_phone_still_escalates():
    text = "I sent GHS 400.00 to you by mistake, kindly refund to 0244123456"
    result = enrich(text, safe_result(), enable_escalation=True)
    assert result["band"] == "suspicious"
    assert result["band_source"] == "heuristic_escalation"


def test_brand_lookalike_link_still_escalates():
    text = "check your bonus at mtn-rewards-claim.com today"
    result = enrich(text, safe_result(), enable_escalation=True)
    assert result["band"] == "suspicious"
    assert result["band_source"] == "heuristic_escalation"


def test_negated_pin_safety_footer_does_not_trigger_pin_request():
    # Real MTN/Telecel confirmations append this exact safety footer -- it
    # must NOT be treated as a scam asking for your PIN.
    text = (
        "confirmed. you have received ghs2,039.42 from your <name> account "
        "on 2026-01-22 at 09:05:08. your telecel cash balance is ghs38.00. "
        "stay alert. never share your pin or otp with anyone or click "
        "unknown links. protect your personal information."
    )
    result = enrich(text, safe_result())
    assert "pin_request" not in ids(result)
    assert result["band"] == "safe"
    assert result["band_source"] == "model"
