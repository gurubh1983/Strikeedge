from __future__ import annotations

from app.services.signals import signal_detector


def test_detect_crossovers_rsi_above() -> None:
    previous = {"rsi_14": 59.0, "macd": 0.1, "macd_signal": 0.2}
    current = {"rsi_14": 61.0, "macd": 0.3, "macd_signal": 0.2}
    events = signal_detector.detect_crossovers("NIFTY_24000_CE", "1m", previous, current)
    assert any(event["indicator"] == "rsi_14" for event in events)


def test_detect_crossovers_macd_below() -> None:
    previous = {"rsi_14": 45.0, "macd": 0.5, "macd_signal": 0.4}
    current = {"rsi_14": 44.0, "macd": 0.2, "macd_signal": 0.3}
    events = signal_detector.detect_crossovers("NIFTY_24000_CE", "1m", previous, current)
    assert any(event["indicator"] == "macd" and "below" in event["message"] for event in events)
