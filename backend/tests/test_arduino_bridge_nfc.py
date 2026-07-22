"""
Pytest unit tests for ArduinoBridge NFC payment handling.
Covers BE-01 through BE-04 as defined in plan 20.1-02.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure dashboard package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dashboard.arduino_bridge import ArduinoBridge


@pytest.fixture
def bridge(monkeypatch):
    """ArduinoBridge with mocked serial and socketio — no real threads started."""
    monkeypatch.setenv("CASHIER_JWT", "test-jwt-token")
    socketio_mock = MagicMock()
    arduino_mock = MagicMock()
    arduino_mock.is_open = True
    # Patch _start_serial_thread so no background thread is started
    with patch.object(ArduinoBridge, "_start_serial_thread", lambda self: None):
        b = ArduinoBridge(arduino_serial=arduino_mock, socketio=socketio_mock)
    return b


def test_nfc_payment_event_emitted(bridge):
    """BE-01: NFC|<token> line emits nfc_payment with token payload."""
    token = "A" * 48
    bridge._parse_line(f"NFC|{token}")
    bridge.socketio.emit.assert_any_call("nfc_payment", {"token": token})


def test_nfc_fail_emits_error_result(bridge):
    """BE-02: ERROR|NFC_FAIL emits nfc_payment_result with success=False."""
    bridge._parse_line("ERROR|NFC_FAIL")
    bridge.socketio.emit.assert_called_once_with(
        "nfc_payment_result", {"success": False, "error": "NFC_FAIL"}
    )


def test_post_nfc_payment_calls_requests(bridge, monkeypatch):
    """BE-03: _post_nfc_payment calls requests.post with correct args."""
    monkeypatch.setenv("CASHIER_JWT", "my-secret-jwt")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:5001")
    with patch("dashboard.arduino_bridge.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        bridge._post_nfc_payment("B" * 48)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "/api/nfc/pay" in args[0]
        assert kwargs["json"] == {"token": "B" * 48}
        assert "Authorization" in kwargs["headers"]
        assert "my-secret-jwt" in kwargs["headers"]["Authorization"]


def test_missing_cashier_jwt_does_not_raise(bridge, monkeypatch):
    """BE-04: Missing CASHIER_JWT logs warning, does not raise."""
    monkeypatch.delenv("CASHIER_JWT", raising=False)
    with patch("dashboard.arduino_bridge.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        try:
            bridge._post_nfc_payment("C" * 48)
        except Exception as e:
            pytest.fail(f"_post_nfc_payment raised unexpectedly: {e}")


def test_r3_card_line_reaches_one_shot_callback(bridge):
    """UNO R3's serial CARD| protocol drives the registration/cashier callback."""
    callback = MagicMock()
    bridge.reading_active = True
    bridge.current_callback = callback

    bridge._parse_line("CARD|00A1B2C3")

    callback.assert_called_once_with("00A1B2C3")
    assert bridge.reading_active is False
    assert bridge.current_callback is None
