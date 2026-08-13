from api.redact import redact


def test_redacts_amount_and_name():
    out, counts = redact(
        "Confirmed. You have received GHS50.00 from KWAME. Your new balance is GHS212.30."
    )
    assert "KWAME" not in out
    assert "50.00" not in out
    assert "212.30" not in out
    assert "<NAME>" in out
    assert "<AMOUNT>" in out
    assert counts["name"] == 1
    assert counts["amount"] == 2


def test_redacts_phone():
    out, counts = redact("Kindly refund within 10 minutes to 0244123456")
    assert "0244123456" not in out
    assert "<PHONE>" in out
    assert counts["phone"] == 1


def test_redacts_url():
    out, counts = redact("Verify at https://momo-verify.gh/x now")
    assert "momo-verify.gh" not in out
    assert "<URL>" in out
    assert counts["url"] == 1


def test_redacts_long_digit_ref():
    out, counts = redact("Ref TXN-9921-04 confirmed")
    assert "9921" not in out
    assert "<REF>" in out
    assert counts["ref"] >= 1


def test_redacts_two_names():
    out, counts = redact("Payment received. GHS 120.00 from AMA OWUSU. Balance GHS 340.50.")
    assert "AMA OWUSU" not in out
    assert counts["name"] == 1
    assert counts["amount"] == 2


def test_truncates_to_max_length():
    out, _ = redact("x" * 5000)
    assert len(out) <= 1000
