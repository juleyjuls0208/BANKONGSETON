"""Standalone cashier POS route guardrails for S04 verification."""

from unittest.mock import MagicMock

from tests.conftest import _make_cashier_token
from tests.test_cashier_routes import _ws_factory


def test_cashier_products_route_returns_products(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    products_ws = MagicMock()
    products_ws.get_all_records.return_value = [
        {"ID": "P001", "Name": "Burger", "Category": "Food", "Price": "55", "Active": "TRUE"},
        {"ID": "P002", "Name": "Iced Tea", "Category": "Drinks", "Price": "25", "Active": "FALSE"},
    ]
    db.worksheet.side_effect = _ws_factory(**{"Products": products_ws})

    client = app.test_client()
    client.set_cookie("jwt_token", token)

    resp = client.get("/cashier/api/products")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data.get("products"), list)
    assert data["products"][0]["name"] == "Burger"
    assert data["products"][0]["price"] == 55.0


def test_cashier_process_sale_rejects_invalid_payload(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    client = app.test_client()
    client.set_cookie("jwt_token", token)

    resp = client.post("/cashier/api/process-sale", json={"items": [], "total": 0})
    assert resp.status_code == 400


def test_cashier_process_sale_sets_pending_transaction(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    payload = {"items": [{"name": "Pancit", "price": 45.0, "qty": 1}], "total": 45.0}

    client = app.test_client()
    client.set_cookie("jwt_token", token)

    resp = client.post("/cashier/api/process-sale", json=payload)
    assert resp.status_code == 200
    assert resp.get_json().get("status") == "waiting_for_card"

    with client.session_transaction() as sess:
        pending = sess.get("pending_transaction")

    assert pending is not None
    assert pending["total"] == 45.0
    assert pending["items"][0]["name"] == "Pancit"
