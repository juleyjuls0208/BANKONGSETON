"""Standalone cashier Arduino/QR route guardrails for S04 verification."""

import time
from unittest.mock import MagicMock, patch

from tests.conftest import _make_cashier_token


def test_cashier_queue_status_route_returns_queue_snapshot(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    queue = MagicMock()
    queue.get_status.return_value = {"pending": 2, "failed": 0, "synced": 4}

    client = app.test_client()
    client.set_cookie("jwt_token", token)

    with patch("offline_queue.get_offline_queue", return_value=queue):
        resp = client.get("/cashier/api/queue/status")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["pending"] == 2
    assert data["synced"] == 4


def test_cashier_arduino_wifi_status_reflects_recent_heartbeat(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    app.config["ARDUINO_WIFI_OFFLINE_S"] = 60
    app.arduino_last_heartbeat = time.time()

    client = app.test_client()
    client.set_cookie("jwt_token", token)

    resp = client.get("/cashier/api/arduino-wifi-status")
    assert resp.status_code == 200
    assert resp.get_json().get("online") is True


def test_cashier_qr_generate_route_creates_pending_token(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    client = app.test_client()
    client.set_cookie("jwt_token", token)

    resp = client.post(
        "/cashier/api/qr-generate",
        json={
            "items": [{"name": "Siomai", "price": 35.0, "qty": 1}],
            "total": 35.0,
        },
    )
    assert resp.status_code == 200

    data = resp.get_json()
    assert data.get("token")
    assert "/api/qr/" in data.get("url", "")
