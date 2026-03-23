"""Standalone cashier payment route guardrails for S04 verification."""

from unittest.mock import MagicMock

from tests.conftest import _make_cashier_token, _set_pending
from tests.test_cashier_routes import _ITEMS, _TOTAL, _VALID_UID, _money_ws, _safe_users_ws, _ws_factory


def test_cashier_complete_sale_route_success(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    money_ws = _money_ws(
        [{"MoneyCardNumber": _VALID_UID, "Balance": 500, "Status": "active"}]
    )
    trans_ws = MagicMock()

    db.worksheet.side_effect = _ws_factory(
        **{
            "Money Accounts": money_ws,
            "Transactions Log": trans_ws,
            "Users": _safe_users_ws(),
        }
    )

    client = app.test_client()
    client.set_cookie("jwt_token", token)
    _set_pending(client, _ITEMS, float(_TOTAL))

    resp = client.post("/cashier/api/complete-sale", json={"card_uid": _VALID_UID})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert float(data.get("new_balance", 0)) == 450.0


def test_cashier_complete_sale_nfc_route_success(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    virtual_cards_ws = MagicMock()
    virtual_cards_ws.get_all_records.return_value = [
        {
            "VirtualCardToken": "vtoken-123",
            "MoneyCardNumber": _VALID_UID,
            "IsActive": "TRUE",
        }
    ]

    money_ws = _money_ws(
        [{"MoneyCardNumber": _VALID_UID, "Balance": 500, "Status": "active"}]
    )
    trans_ws = MagicMock()

    db.worksheet.side_effect = _ws_factory(
        **{
            "VirtualCards": virtual_cards_ws,
            "Money Accounts": money_ws,
            "Transactions Log": trans_ws,
            "Users": _safe_users_ws(),
        }
    )

    client = app.test_client()
    client.set_cookie("jwt_token", token)
    _set_pending(client, _ITEMS, float(_TOTAL))

    resp = client.post(
        "/cashier/api/complete-sale-nfc",
        json={"virtual_card_token": "vtoken-123"},
    )
    assert resp.status_code == 200
    assert resp.get_json().get("success") is True
    trans_ws.append_row.assert_called_once()
    transaction_row = trans_ws.append_row.call_args.args[0]
    assert isinstance(transaction_row, list)
    assert len(transaction_row) >= 10
    assert str(transaction_row[0]).startswith("TXN-")


def test_cashier_complete_sale_nfc_requires_token(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    client = app.test_client()
    client.set_cookie("jwt_token", token)
    _set_pending(client, _ITEMS, float(_TOTAL))

    resp = client.post("/cashier/api/complete-sale-nfc", json={})
    assert resp.status_code == 400


def test_cashier_complete_sale_nfc_rolls_back_on_non_retryable_log_error(flask_app, db):
    app, _ = flask_app
    token = _make_cashier_token("cashier1", "cashier")

    virtual_cards_ws = MagicMock()
    virtual_cards_ws.get_all_records.return_value = [
        {
            "VirtualCardToken": "vtoken-123",
            "MoneyCardNumber": _VALID_UID,
            "IsActive": "TRUE",
        }
    ]

    money_ws = _money_ws(
        [{"MoneyCardNumber": _VALID_UID, "Balance": 500, "Status": "active"}]
    )
    trans_ws = MagicMock()
    trans_ws.append_row.side_effect = ValueError("row serialization failed")

    db.worksheet.side_effect = _ws_factory(
        **{
            "VirtualCards": virtual_cards_ws,
            "Money Accounts": money_ws,
            "Transactions Log": trans_ws,
            "Users": _safe_users_ws(),
        }
    )

    client = app.test_client()
    client.set_cookie("jwt_token", token)
    _set_pending(client, _ITEMS, float(_TOTAL))

    resp = client.post(
        "/cashier/api/complete-sale-nfc",
        json={"virtual_card_token": "vtoken-123"},
    )

    assert resp.status_code == 503
    assert money_ws.update_cell.call_count == 2
    assert money_ws.update_cell.call_args_list[0].args == (2, 3, 450.0)
    assert money_ws.update_cell.call_args_list[1].args == (2, 3, 500.0)
