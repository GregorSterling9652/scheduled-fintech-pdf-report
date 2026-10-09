from datetime import date

from src.fintech_report import PaymentEvent, render_markdown, risk_label


def test_large_successful_payment_is_marked_for_review_in_report() -> None:
    event = PaymentEvent("evt_high", "Atlas Market", 100_000, "USD", "succeeded", date(2026, 9, 3))
    assert risk_label(event) == "review"
    assert "| evt_high | Atlas Market | 1000.00 USD | succeeded | review |" in render_markdown([event], "2026-09")
