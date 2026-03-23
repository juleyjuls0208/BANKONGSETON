"""Smoke tests for standalone cashier runtime (backend/cashier_app/app.py)."""

from __future__ import annotations

import importlib
import sys

import jwt
from unittest.mock import MagicMock, patch


def _load_standalone_cashier_app(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-standalone-secret")
    monkeypatch.setenv("JWT_SECRET", "test-standalone-jwt")
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "test-sheet-id")
    monkeypatch.setenv("ARDUINO_API_KEY", "test-arduino-key")

    mock_spreadsheet = MagicMock()
    mock_gspread_client = MagicMock()
    mock_gspread_client.open_by_key.return_value = mock_spreadsheet

    module_name = "backend.cashier_app.app"
    if module_name in sys.modules:
        del sys.modules[module_name]

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=MagicMock(),
    ), patch("gspread.authorize", return_value=mock_gspread_client):
        mod = importlib.import_module(module_name)

    return mod.app


def test_standalone_root_redirects_to_native_login(monkeypatch):
    app = _load_standalone_cashier_app(monkeypatch)
    client = app.test_client()

    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_standalone_healthz_and_login_routes(monkeypatch):
    app = _load_standalone_cashier_app(monkeypatch)
    client = app.test_client()

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json().get("ok") is True

    login_page = client.get("/login")
    assert login_page.status_code == 200
    login_html = login_page.get_data(as_text=True)
    assert "/api/login" in login_html
    assert "/cashier/api/login" not in login_html

    # Legacy URL still works but canonicalizes to native login.
    legacy_login = client.get("/cashier/login")
    assert legacy_login.status_code == 302
    assert legacy_login.headers["Location"].endswith("/login")

    # Authenticated root serves POS template that uses native /api endpoints.
    token = jwt.encode(
        {"username": "cashier", "role": "cashier"},
        "test-standalone-jwt",
        algorithm="HS256",
    )
    client.set_cookie("jwt_token", token)
    root_page = client.get("/")
    assert root_page.status_code == 200
    root_html = root_page.get_data(as_text=True)
    assert "/api/products" in root_html
    assert "/cashier/api/products" not in root_html


def test_standalone_arduino_heartbeat_requires_valid_api_key(monkeypatch):
    app = _load_standalone_cashier_app(monkeypatch)
    client = app.test_client()

    unauthorized = client.post("/api/arduino/heartbeat", json={})
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/arduino/heartbeat",
        json={},
        headers={"X-API-Key": "test-arduino-key"},
    )
    assert authorized.status_code == 200
    assert authorized.get_json().get("status") == "ok"

    # Native + legacy QR callback aliases both exist.
    assert client.post("/api/qr-paid", json={}).status_code == 401
    assert client.post("/api/cashier/qr-paid", json={}).status_code == 401
