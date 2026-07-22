"""Regression contracts for registration, cashier accounts, and cashier management."""
from pathlib import Path
from unittest.mock import MagicMock
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
REG_TEMPLATE = ROOT / "backend" / "dashboard" / "templates" / "registration.html"
PANEL_CSS = ROOT / "backend" / "dashboard" / "static" / "css" / "panel.css"
REG_APP = ROOT / "backend" / "dashboard" / "registration_app.py"
CASHIER_TEMPLATE = ROOT / "backend" / "cashier_app" / "templates" / "cashier_index_standalone.html"
DASHBOARD_CASHIER_TEMPLATE = ROOT / "backend" / "dashboard" / "cashier" / "templates" / "cashier_index.html"


def test_registration_success_is_really_hidden_and_rearming_is_guarded():
    template = REG_TEMPLATE.read_text(encoding="utf-8")
    css = PANEL_CSS.read_text(encoding="utf-8")
    source = REG_APP.read_text(encoding="utf-8")

    assert "[hidden]" in css and "display: none !important" in css
    assert "registerRequestInFlight" in template
    assert "if (registerRequestInFlight" in template
    assert "already_connected" in source
    assert "Card reader is already waiting for a card" in source


def test_supabase_adapter_exposes_live_cashier_accounts_and_product_contract():
    from backend import sheets_adapter as adapter

    assert "cashier_accounts" in adapter._TABLES
    assert adapter._TABLE_LOOKUP["cashier accounts"] == "cashier_accounts"
    assert adapter._KEY_COLUMNS["cashier_accounts"] == "AccountID"
    assert adapter._KEY_COLUMNS["products"] == "ID"
    assert adapter._TABLE_COLUMNS["products"][0] == "ID"


def test_cashier_transaction_row_records_account_not_generic_station():
    from backend.cashier_app.cashier_routes import _build_transaction_row

    sheet = MagicMock()
    sheet.row_values.return_value = ["TransactionID", "CashierID"]
    row = _build_transaction_row(
        sheet,
        transaction_id="TX-1",
        timestamp="2026-07-19T21:00:00+08:00",
        student_id="202320112",
        money_card_number="CARD-1",
        transaction_type="Purchase",
        amount=-50,
        balance_before=500,
        balance_after=450,
        cashier_id="cashier-account-1",
    )

    assert row == ["TX-1", "cashier-account-1"]


def test_cashier_standalone_app_imports_from_project_package_context():
    from backend.cashier_app import app

    assert callable(app.create_app)
    assert app._ADAPTER_AVAILABLE is True


def test_shared_backend_services_are_importable_after_cashier_package_load():
    from backend.services import loading_service

    assert loading_service.__file__.replace("\\", "/").endswith("backend/services/loading_service.py")


def test_cashier_management_and_held_cart_are_real_not_dead_navigation():
    template = CASHIER_TEMPLATE.read_text(encoding="utf-8")

    for view in ("register", "history", "students", "inventory"):
        assert f'data-view="{view}"' in template
    for endpoint in ("/history", "/students", "/inventory"):
        assert endpoint in template
    assert "let heldCarts = []" in template
    assert "function holdCart" in template
    assert "function restoreHeldCart" in template
    assert "heldCarts.splice(index, 0, outgoing)" in template
    assert "Void Cart" in template
    assert "Void Item" not in template
    assert "Cashier #042" not in template
    assert "Gabriel Santos" not in template
    assert "user.display_name" in template
    assert "No student selected" in template
    assert "[hidden] { display: none !important; }" in template
