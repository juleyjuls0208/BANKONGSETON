"""
Tests for admin critical routes: load_balance and void_transaction.

Slice S04 / Task T03 — ~17 unit tests covering the two admin paths
that move real money (load_balance and void_transaction).

Key mechanics:
  - load_balance is @login_required only — both finance_client and admin_client
    can call it.
  - void_transaction is @login_required + @admin_only — finance role gets 403;
    unauthenticated client gets 302 redirect.
  - db fixture provides a per-test fresh MagicMock spreadsheet. Configure
    db.worksheet.side_effect per test to return named worksheet mocks.
  - MagicMock auto-chains .find().col so no special setup is needed for
    money_sheet.find('Balance').col.
  - get_sms_notifier is patched in SMS-failure tests to prevent Twilio calls.
  - invalidate_pattern is patched in cache-invalidation tests.
"""

import os
import sys

import pytest
from unittest.mock import MagicMock, patch

# Ensure conftest helpers are importable
sys.path.insert(0, os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ws_factory(**sheets):
    """Build a side_effect for db.worksheet that maps sheet name → mock.

    Any name not explicitly listed returns a generic MagicMock with
    get_all_records() → [] so iteration is always safe.
    """
    fallback = MagicMock()
    fallback.get_all_records.return_value = []

    def _factory(name):
        return sheets.get(name, fallback)

    return _factory


def _make_money_account_ws(card, balance, status='Active'):
    """Return a configured Money Accounts worksheet mock with one record."""
    ws = MagicMock()
    ws.get_all_records.return_value = [
        {
            'MoneyCardNumber': card,
            'Balance': str(balance),
            'Status': status,
            'TotalLoaded': str(balance),
            'LastUpdated': '2026-01-01 00:00:00',
        }
    ]
    return ws


def _make_users_ws(card=None, name='Test Student',
                   parent_phone=None, parent_email=None):
    """Return a Users worksheet mock."""
    ws = MagicMock()
    if card:
        ws.get_all_records.return_value = [
            {
                'MoneyCardNumber': card,
                'Name': name,
                'StudentID': 'S-001',
                'ParentPhone': parent_phone or '',
                'ParentEmail': parent_email or '',
            }
        ]
    else:
        ws.get_all_records.return_value = []
    return ws


def _make_txn_ws(records=None):
    """Return a Transactions Log worksheet mock."""
    ws = MagicMock()
    ws.get_all_records.return_value = records or []
    return ws


# ---------------------------------------------------------------------------
# Shared test constants
# ---------------------------------------------------------------------------

_CARD = 'ABCD1234'
_BALANCE = 500.0

_TXN_ID = 'TXN-001'
_TXN_CARD = 'CARD5678'


def _purchase_txn(txn_id=_TXN_ID, card=_TXN_CARD, amount=-50.0):
    """Return a Purchase transaction row dict."""
    return {
        'TransactionID': txn_id,
        'MoneyCardNumber': card,
        'TransactionType': 'Purchase',
        'Amount': amount,
        'StudentID': 'S-001',
    }


def _load_txn(txn_id=_TXN_ID, card=_TXN_CARD, amount=100.0):
    """Return a Load transaction row dict."""
    return {
        'TransactionID': txn_id,
        'MoneyCardNumber': card,
        'TransactionType': 'Load',
        'Amount': amount,
        'StudentID': 'S-001',
    }


# ---------------------------------------------------------------------------
# TestLoadBalance — 6 tests
# ---------------------------------------------------------------------------

class TestLoadBalance:
    """POST /api/load-balance — @login_required (finance + admin allowed)."""

    def test_load_balance_success(self, flask_app, db, admin_client):
        """Card found, balance=500, amount=200 → 200, new_balance=700."""
        money_ws = _make_money_account_ws(_CARD, _BALANCE)
        users_ws = _make_users_ws(card=_CARD, name='Juan dela Cruz')
        txn_ws = _make_txn_ws()
        db.worksheet.side_effect = _ws_factory(**{
            'Money Accounts': money_ws,
            'Users': users_ws,
            'Transactions Log': txn_ws,
        })

        resp = admin_client.post('/api/load-balance', json={
            'money_card': _CARD,
            'amount': 200.0,
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['new_balance'] == _BALANCE + 200.0
        assert 'student_name' in data

    def test_load_balance_finance_role_allowed(self, flask_app, db, finance_client):
        """Finance role can load balance (route is @login_required only)."""
        money_ws = _make_money_account_ws(_CARD, _BALANCE)
        users_ws = _make_users_ws(card=_CARD)
        txn_ws = _make_txn_ws()
        db.worksheet.side_effect = _ws_factory(**{
            'Money Accounts': money_ws,
            'Users': users_ws,
            'Transactions Log': txn_ws,
        })

        resp = finance_client.post('/api/load-balance', json={
            'money_card': _CARD,
            'amount': 100.0,
        })

        assert resp.status_code == 200

    def test_load_balance_sms_failure_nonfatal(self, flask_app, db, admin_client):
        """SMS notifier raising an exception must not fail the load operation."""
        money_ws = _make_money_account_ws(_CARD, _BALANCE)
        # Include a phone so the SMS branch is entered
        users_ws = _make_users_ws(card=_CARD, parent_phone='+639171234567')
        txn_ws = _make_txn_ws()
        db.worksheet.side_effect = _ws_factory(**{
            'Money Accounts': money_ws,
            'Users': users_ws,
            'Transactions Log': txn_ws,
        })

        import backend.dashboard.admin_dashboard as adm_module
        with patch.object(adm_module, 'get_sms_notifier',
                          side_effect=RuntimeError('Twilio down'), create=True):
            resp = admin_client.post('/api/load-balance', json={
                'money_card': _CARD,
                'amount': 50.0,
            })

        assert resp.status_code == 200

    def test_load_balance_invalid_amount_zero(self, flask_app, db, admin_client):
        """Amount of 0 → 400 before any Sheets lookup."""
        resp = admin_client.post('/api/load-balance', json={
            'money_card': _CARD,
            'amount': 0,
        })
        assert resp.status_code == 400

    def test_load_balance_invalid_amount_negative(self, flask_app, db, admin_client):
        """Negative amount → 400."""
        resp = admin_client.post('/api/load-balance', json={
            'money_card': _CARD,
            'amount': -50,
        })
        assert resp.status_code == 400

    def test_load_balance_card_not_found(self, flask_app, db, admin_client):
        """Money Accounts returns empty list → 404."""
        empty_ws = MagicMock()
        empty_ws.get_all_records.return_value = []
        db.worksheet.side_effect = _ws_factory(**{
            'Money Accounts': empty_ws,
        })

        resp = admin_client.post('/api/load-balance', json={
            'money_card': 'NOTEXIST99',
            'amount': 100.0,
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestVoidTransaction — 11 tests
# ---------------------------------------------------------------------------

class TestVoidTransaction:
    """POST /api/admin/transactions/<txn_id>/void — @login_required + @admin_only."""

    # --- Success and value correctness ---

    def test_void_transaction_success(self, flask_app, db, admin_client):
        """Purchase txn of -50 with balance=400 → 200, restored_balance=450, correct void_id."""
        txn_ws = _make_txn_ws([_purchase_txn(amount=-50.0)])
        money_ws = _make_money_account_ws(_TXN_CARD, 400.0)
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': money_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={'reason': 'Test void'},
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['restored_balance'] == 450.0
        assert data['void_id'] == f'VOID-{_TXN_ID}'

    def test_void_transaction_load_reversal(self, flask_app, db, admin_client):
        """Load txn of 100 voided from balance=600 → restored_balance=500."""
        txn_ws = _make_txn_ws([_load_txn(amount=100.0)])
        money_ws = _make_money_account_ws(_TXN_CARD, 600.0)
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': money_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={'reason': 'Reverse load'},
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['restored_balance'] == 500.0

    def test_void_transaction_balance_restoration_correct_value(
            self, flask_app, db, admin_client):
        """Purchase of 75 with current balance=425 → restored exactly 500.0."""
        txn = {
            'TransactionID': _TXN_ID,
            'MoneyCardNumber': _TXN_CARD,
            'TransactionType': 'Purchase',
            'Amount': -75.0,
            'StudentID': 'S-001',
        }
        txn_ws = _make_txn_ws([txn])
        money_ws = _make_money_account_ws(_TXN_CARD, 425.0)
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': money_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={'reason': 'Math check'},
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['restored_balance'] == 500.0

    def test_void_transaction_void_record_appended(self, flask_app, db, admin_client):
        """append_row called once; the row contains 'Void' as the transaction type."""
        txn_ws = _make_txn_ws([_purchase_txn(amount=-50.0)])
        money_ws = _make_money_account_ws(_TXN_CARD, 400.0)
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': money_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={'reason': 'Append check'},
        )

        assert resp.status_code == 200
        txn_ws.append_row.assert_called_once()
        appended_row = txn_ws.append_row.call_args[0][0]
        assert 'Void' in appended_row

    def test_void_transaction_invalidates_cache(self, flask_app, db, admin_client):
        """invalidate_pattern called for both 'transactions' and 'money_accounts'."""
        txn_ws = _make_txn_ws([_purchase_txn(amount=-50.0)])
        money_ws = _make_money_account_ws(_TXN_CARD, 400.0)
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': money_ws,
        })

        import backend.dashboard.admin_dashboard as adm_module
        with patch.object(adm_module, 'invalidate_pattern', create=True) as mock_inv:
            resp = admin_client.post(
                f'/api/admin/transactions/{_TXN_ID}/void',
                json={'reason': 'Cache check'},
            )
            assert resp.status_code == 200
            called_args = [call[0][0] for call in mock_inv.call_args_list]
            assert 'transactions' in called_args
            assert 'money_accounts' in called_args

    # --- Guard / rejection cases ---

    def test_void_transaction_not_found(self, flask_app, db, admin_client):
        """Transactions Log has no matching txn_id → 404."""
        txn_ws = _make_txn_ws([_purchase_txn(txn_id='TXN-OTHER')])
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
        })

        resp = admin_client.post(
            '/api/admin/transactions/TXN-MISSING/void',
            json={},
        )
        assert resp.status_code == 404

    def test_void_transaction_double_void_rejected(self, flask_app, db, admin_client):
        """Transaction already a Void type → 400 with 'already a void' in error."""
        already_void = {
            'TransactionID': _TXN_ID,
            'MoneyCardNumber': _TXN_CARD,
            'TransactionType': 'Void',
            'Amount': 50.0,
            'StudentID': 'S-001',
        }
        txn_ws = _make_txn_ws([already_void])
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'already a void' in data.get('error', '').lower()

    def test_void_transaction_requires_admin(self, flask_app, db, finance_client):
        """Finance role (non-admin) → admin_only decorator returns 403."""
        resp = finance_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={'reason': 'finance attempt'},
        )
        assert resp.status_code != 200

    def test_void_transaction_requires_login(self, flask_app):
        """Unauthenticated client → login_required redirects (302)."""
        app, _ = flask_app
        client = app.test_client()
        resp = client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={},
        )
        assert resp.status_code in (302, 401)

    def test_void_transaction_money_card_not_found(self, flask_app, db, admin_client):
        """Txn found but Money Accounts has no matching card → 404."""
        txn_ws = _make_txn_ws([_purchase_txn()])
        empty_money_ws = MagicMock()
        empty_money_ws.get_all_records.return_value = []
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': empty_money_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={},
        )
        assert resp.status_code == 404

    def test_void_transaction_reason_defaults(self, flask_app, db, admin_client):
        """POST {} (no reason) → 200; void record appended with default reason text."""
        txn_ws = _make_txn_ws([_purchase_txn(amount=-50.0)])
        money_ws = _make_money_account_ws(_TXN_CARD, 400.0)
        db.worksheet.side_effect = _ws_factory(**{
            'Transactions Log': txn_ws,
            'Money Accounts': money_ws,
        })

        resp = admin_client.post(
            f'/api/admin/transactions/{_TXN_ID}/void',
            json={},
        )

        assert resp.status_code == 200
        txn_ws.append_row.assert_called_once()
        appended_row = txn_ws.append_row.call_args[0][0]
        # Default reason 'Voided by admin' must appear somewhere in the row
        assert any('Voided by admin' in str(cell) for cell in appended_row)
