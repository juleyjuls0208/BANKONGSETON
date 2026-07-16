"""
Tests for Fraud Alert API endpoints and Google Sheets persistence.
Slice S01 / Task T01 — verification suite.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import os
import sys

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ---------------------------------------------------------------------------
# FraudDetector unit tests (no network, no Flask)
# ---------------------------------------------------------------------------

from backend.fraud_detection import (
    FraudDetector, FraudAlert, FraudType, RiskLevel, get_fraud_detector
)


@pytest.fixture(autouse=True)
def reset_fraud_detector():
    """Reset the module-level singleton between tests."""
    import backend.fraud_detection as fd
    fd._fraud_detector = None
    yield
    fd._fraud_detector = None


@pytest.fixture
def detector():
    return FraudDetector()


# ── Sheet persistence helpers ────────────────────────────────────────────────

class TestLoadFromSheets:
    def test_load_alerts_populates_list(self, detector):
        fraud_ws = MagicMock()
        fraud_ws.get_all_records.return_value = [
            {
                'AlertID': 'ALERT-1',
                'MoneyCard': 'CARD001',
                'FraudType': 'velocity',
                'RiskLevel': 'high',
                'Description': 'Test alert',
                'CreatedAt': '2026-03-01T10:00:00+08:00',
                'Resolved': 'False',
                'ResolvedAt': '',
                'ResolutionNotes': '',
                'AutoAction': '',
            }
        ]
        suspended_ws = MagicMock()
        suspended_ws.get_all_records.return_value = []

        detector.load_from_sheets(fraud_ws, suspended_ws)

        assert len(detector.alerts) == 1
        assert detector.alerts[0].id == 'ALERT-1'
        assert detector.alerts[0].money_card == 'CARD001'
        assert detector.alerts[0].risk_level == RiskLevel.HIGH

    def test_load_suspended_cards(self, detector):
        fraud_ws = MagicMock()
        fraud_ws.get_all_records.return_value = []
        suspended_ws = MagicMock()
        suspended_ws.get_all_records.return_value = [
            {
                'MoneyCard': 'CARD999',
                'Reason': 'Stolen',
                'SuspendedAt': '2026-03-01T09:00:00+08:00',
                'AutoSuspended': 'False',
            }
        ]

        detector.load_from_sheets(fraud_ws, suspended_ws)

        assert 'CARD999' in detector.suspended_cards
        assert detector.suspended_cards['CARD999']['reason'] == 'Stolen'

    def test_load_handles_sheet_error_gracefully(self, detector):
        fraud_ws = MagicMock()
        fraud_ws.get_all_records.side_effect = Exception("API error")
        suspended_ws = MagicMock()
        suspended_ws.get_all_records.return_value = []

        # Should not raise
        detector.load_from_sheets(fraud_ws, suspended_ws)
        assert detector.alerts == []

    def test_load_skips_rows_without_alert_id(self, detector):
        fraud_ws = MagicMock()
        fraud_ws.get_all_records.return_value = [
            {'AlertID': '', 'MoneyCard': 'X', 'FraudType': 'velocity',
             'RiskLevel': 'low', 'Description': '', 'CreatedAt': '',
             'Resolved': 'False', 'ResolvedAt': '', 'ResolutionNotes': '', 'AutoAction': ''}
        ]
        suspended_ws = MagicMock()
        suspended_ws.get_all_records.return_value = []

        detector.load_from_sheets(fraud_ws, suspended_ws)
        assert len(detector.alerts) == 0


class TestSaveAlertToSheet:
    def test_appends_row(self, detector):
        alert = FraudAlert(
            money_card='CARD001',
            fraud_type=FraudType.VELOCITY,
            risk_level=RiskLevel.HIGH,
            description='Test',
        )
        ws = MagicMock()

        result = detector.save_alert_to_sheet(ws, alert)

        assert result is True
        ws.append_row.assert_called_once()
        row = ws.append_row.call_args[0][0]
        assert row[0] == alert.id
        assert row[1] == 'CARD001'
        assert row[2] == 'velocity'
        assert row[3] == 'high'

    def test_returns_false_on_error(self, detector):
        ws = MagicMock()
        ws.append_row.side_effect = Exception("Quota exceeded")
        alert = FraudAlert('C', FraudType.VELOCITY, RiskLevel.LOW, 'x')

        result = detector.save_alert_to_sheet(ws, alert)
        assert result is False


class TestUpdateAlertInSheet:
    def test_updates_resolved_columns(self, detector):
        alert = FraudAlert('CARD001', FraudType.VELOCITY, RiskLevel.HIGH, 'Test')
        alert.id = 'ALERT-42'
        alert.resolve('manual review')

        ws = MagicMock()
        ws.get_all_records.return_value = [
            {'AlertID': 'ALERT-42', 'MoneyCard': 'CARD001'}
        ]

        result = detector.update_alert_in_sheet(ws, alert)

        assert result is True
        # update_cell called for Resolved(col7), ResolvedAt(col8), Notes(col9)
        calls = ws.update_cell.call_args_list
        assert len(calls) == 3
        # Each call: (row, col, value) — check row=2 and col=7 for first call
        first_call_args = calls[0][0]
        assert first_call_args[0] == 2   # row 2 (header+1)
        assert first_call_args[1] == 7   # col 7 = Resolved

    def test_returns_false_when_not_found(self, detector):
        alert = FraudAlert('CARD001', FraudType.VELOCITY, RiskLevel.HIGH, 'Test')
        alert.id = 'NONEXISTENT'
        ws = MagicMock()
        ws.get_all_records.return_value = []

        result = detector.update_alert_in_sheet(ws, alert)
        assert result is False


class TestSaveSuspendedCard:
    def test_appends_new_card(self, detector):
        ws = MagicMock()
        ws.get_all_records.return_value = []

        result = detector.save_suspended_card_to_sheet(ws, 'CARD001', {
            'reason': 'Stolen',
            'suspended_at': '2026-03-01T10:00:00',
            'auto_suspended': False,
        })

        assert result is True
        ws.append_row.assert_called_once()
        row = ws.append_row.call_args[0][0]
        assert row[0] == 'CARD001'
        assert row[1] == 'Stolen'

    def test_updates_existing_card(self, detector):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {'MoneyCard': 'CARD001', 'Reason': 'old'}
        ]

        result = detector.save_suspended_card_to_sheet(ws, 'CARD001', {
            'reason': 'Updated reason',
            'suspended_at': '2026-03-01T10:00:00',
            'auto_suspended': False,
        })

        assert result is True
        ws.update.assert_called_once()


class TestRemoveSuspendedCard:
    def test_deletes_row(self, detector):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {'MoneyCard': 'CARD001'}
        ]

        result = detector.remove_suspended_card_from_sheet(ws, 'CARD001')

        assert result is True
        ws.delete_rows.assert_called_once_with(2)

    def test_returns_false_when_not_found(self, detector):
        ws = MagicMock()
        ws.get_all_records.return_value = []

        result = detector.remove_suspended_card_from_sheet(ws, 'GHOST')
        assert result is False


# ---------------------------------------------------------------------------
# Flask route tests (mocked Sheets + auth)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def flask_app():
    """Create Flask test client with mocked Sheets and env vars.

    admin_dashboard.py calls get_sheets_client() at module level.  The module
    may already be cached in sys.modules from other tests in this file.  The
    safe approach is to:
      1. Set env vars
      2. Import the module (it's already cached or we accept it may fail on
         first import in isolation — both cases are handled)
      3. Replace adm.db and adm.get_sheets_client on the already-live module
    """
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key-for-fraud-tests'
    os.environ['GOOGLE_SHEETS_ID'] = 'fake-sheet-id'
    os.environ['ADMIN_USERNAME'] = 'admin'
    os.environ['ADMIN_PASSWORD'] = 'adminpass'
    os.environ['FINANCE_USERNAME'] = 'finance'
    os.environ['FINANCE_PASSWORD'] = 'financepass'

    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheets.return_value = []
    mock_spreadsheet.add_worksheet.return_value = MagicMock()
    mock_spreadsheet.worksheet.return_value = MagicMock()

    # Ensure admin_dashboard is importable by patching the gspread chain at the
    # lowest level before the module-level `db = get_sheets_client()` runs.
    creds_patch = patch(
        'google.oauth2.service_account.Credentials.from_service_account_file',
        return_value=MagicMock()
    )
    gspread_patch = patch('gspread.authorize', return_value=MagicMock(
        open_by_key=MagicMock(return_value=mock_spreadsheet)
    ))

    creds_patch.start()
    gspread_patch.start()

    try:
        import backend.dashboard.web_app as adm
    except Exception:
        pass  # module may already be cached from earlier test classes

    import backend.dashboard.web_app as adm

    # Override db on the live module object for all request-time calls
    adm.db = mock_spreadsheet
    adm.get_sheets_client = lambda: mock_spreadsheet

    creds_patch.stop()
    gspread_patch.stop()

    adm.app.config['TESTING'] = True
    adm.app.config['WTF_CSRF_ENABLED'] = False
    yield adm.app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def admin_session(client):
    """Log in as admin and return the client."""
    client.post('/login', json={'username': 'admin', 'password': 'adminpass'})
    return client


@pytest.fixture
def finance_session(client):
    """Log in as finance and return the client."""
    client.post('/login', json={'username': 'finance', 'password': 'financepass'})
    return client


def _patch_detector(detector_instance):
    """Context manager: replace the module-level detector used by routes."""
    import backend.dashboard.web_app as adm
    return patch.object(adm, '_get_fraud_detector_with_sheets', return_value=detector_instance)


def _patch_ensure_sheets(fraud_ws=None, suspended_ws=None):
    import backend.dashboard.web_app as adm
    return patch.object(
        adm, '_ensure_fraud_sheets',
        return_value=(fraud_ws or MagicMock(), suspended_ws or MagicMock())
    )


# ── GET /api/fraud/alerts ────────────────────────────────────────────────────

class TestGetFraudAlertsRoute:
    def test_returns_alert_list(self, admin_session):
        det = FraudDetector()
        a = FraudAlert('CARD001', FraudType.VELOCITY, RiskLevel.HIGH, 'desc')
        det.alerts.append(a)

        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/alerts')

        assert resp.status_code == 200
        body = resp.get_json()
        assert 'alerts' in body
        assert body['count'] == 1
        assert body['alerts'][0]['money_card'] == 'CARD001'

    def test_unresolved_only_filter(self, admin_session):
        det = FraudDetector()
        a1 = FraudAlert('CARD001', FraudType.VELOCITY, RiskLevel.HIGH, 'unresolved')
        a2 = FraudAlert('CARD002', FraudType.VELOCITY, RiskLevel.LOW, 'resolved')
        a2.resolve('done')
        det.alerts.extend([a1, a2])

        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/alerts?unresolved_only=true')

        body = resp.get_json()
        assert body['count'] == 1
        assert body['alerts'][0]['resolved'] is False

    def test_requires_login(self, client):
        resp = client.get('/api/fraud/alerts')
        assert resp.status_code in (302, 401)

    def test_risk_level_filter(self, admin_session):
        det = FraudDetector()
        det.alerts.append(FraudAlert('A', FraudType.VELOCITY, RiskLevel.HIGH, 'h'))
        det.alerts.append(FraudAlert('B', FraudType.VELOCITY, RiskLevel.LOW, 'l'))

        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/alerts?risk_level=high')

        body = resp.get_json()
        assert all(a['risk_level'] == 'high' for a in body['alerts'])


# ── POST /api/fraud/alerts/<id>/resolve ─────────────────────────────────────

class TestResolveAlertRoute:
    def test_resolves_existing_alert(self, admin_session):
        det = FraudDetector()
        a = FraudAlert('CARD001', FraudType.VELOCITY, RiskLevel.HIGH, 'test')
        det.alerts.append(a)
        alert_id = a.id

        with _patch_detector(det), _patch_ensure_sheets():
            resp = admin_session.post(
                f'/api/fraud/alerts/{alert_id}/resolve',
                json={'notes': 'Reviewed, no issue'}
            )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert det.alerts[0].resolved is True
        assert det.alerts[0].resolution_notes == 'Reviewed, no issue'

    def test_returns_404_for_unknown_alert(self, admin_session):
        det = FraudDetector()
        with _patch_detector(det), _patch_ensure_sheets():
            resp = admin_session.post(
                '/api/fraud/alerts/NONEXISTENT/resolve',
                json={'notes': ''}
            )
        assert resp.status_code == 404

    def test_requires_login(self, client):
        resp = client.post('/api/fraud/alerts/X/resolve', json={})
        assert resp.status_code in (302, 401)


# ── POST /api/fraud/cards/<uid>/suspend ─────────────────────────────────────

class TestSuspendCardRoute:
    def test_suspends_card(self, admin_session):
        det = FraudDetector()
        with _patch_detector(det), _patch_ensure_sheets():
            resp = admin_session.post(
                '/api/fraud/cards/CARD001/suspend',
                json={'reason': 'Lost card reported'}
            )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert 'CARD001' in det.suspended_cards

    def test_requires_admin_role(self, finance_session):
        det = FraudDetector()
        with _patch_detector(det), _patch_ensure_sheets():
            resp = finance_session.post(
                '/api/fraud/cards/CARD001/suspend',
                json={'reason': 'test'}
            )
        assert resp.status_code == 403

    def test_requires_login(self, client):
        resp = client.post('/api/fraud/cards/CARD001/suspend', json={})
        assert resp.status_code in (302, 401)


# ── POST /api/fraud/cards/<uid>/unsuspend ───────────────────────────────────

class TestUnsuspendCardRoute:
    def test_unsuspends_card(self, admin_session):
        det = FraudDetector()
        det.suspend_card('CARD001', 'test reason')

        with _patch_detector(det), _patch_ensure_sheets():
            resp = admin_session.post('/api/fraud/cards/CARD001/unsuspend')

        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        assert 'CARD001' not in det.suspended_cards

    def test_returns_404_for_non_suspended_card(self, admin_session):
        det = FraudDetector()
        with _patch_detector(det), _patch_ensure_sheets():
            resp = admin_session.post('/api/fraud/cards/GHOST/unsuspend')
        assert resp.status_code == 404

    def test_requires_admin_role(self, finance_session):
        det = FraudDetector()
        det.suspend_card('CARD001', 'test')
        with _patch_detector(det), _patch_ensure_sheets():
            resp = finance_session.post('/api/fraud/cards/CARD001/unsuspend')
        assert resp.status_code == 403


# ── GET /api/fraud/suspended ─────────────────────────────────────────────────

class TestGetSuspendedRoute:
    def test_returns_suspended_list(self, admin_session):
        det = FraudDetector()
        det.suspend_card('CARD001', 'reason A')
        det.suspend_card('CARD002', 'reason B')

        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/suspended')

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['count'] == 2
        cards = {item['card'] for item in body['suspended']}
        assert 'CARD001' in cards
        assert 'CARD002' in cards

    def test_returns_empty_when_none_suspended(self, admin_session):
        det = FraudDetector()
        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/suspended')
        assert resp.get_json()['count'] == 0

    def test_requires_login(self, client):
        resp = client.get('/api/fraud/suspended')
        assert resp.status_code in (302, 401)


# ── GET /api/fraud/stats ─────────────────────────────────────────────────────

class TestGetFraudStatsRoute:
    def test_returns_required_fields(self, admin_session):
        det = FraudDetector()
        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/stats')

        assert resp.status_code == 200
        body = resp.get_json()
        for field in ('total_alerts', 'unresolved_alerts', 'today_alerts', 'suspended_cards'):
            assert field in body, f"Missing field: {field}"

    def test_counts_are_accurate(self, admin_session):
        det = FraudDetector()
        a1 = FraudAlert('A', FraudType.VELOCITY, RiskLevel.HIGH, 'x')
        a2 = FraudAlert('B', FraudType.VELOCITY, RiskLevel.LOW, 'y')
        a2.resolve('done')
        det.alerts.extend([a1, a2])
        det.suspend_card('CARD001', 'r')

        with _patch_detector(det):
            resp = admin_session.get('/api/fraud/stats')

        body = resp.get_json()
        assert body['total_alerts'] == 2
        assert body['unresolved_alerts'] == 1
        assert body['suspended_cards'] == 1

    def test_requires_login(self, client):
        resp = client.get('/api/fraud/stats')
        assert resp.status_code in (302, 401)


# ── ensure_fraud_sheet creates worksheet with headers ───────────────────────

class TestEnsureFraudSheets:
    def test_creates_fraud_alerts_sheet_if_missing(self):
        mock_db = MagicMock()
        mock_fraud_ws = MagicMock()
        mock_suspended_ws = MagicMock()
        call_count = [0]

        def _add_worksheet(**kwargs):
            call_count[0] += 1
            return mock_fraud_ws if kwargs.get('title') == 'Fraud Alerts' else mock_suspended_ws

        mock_db.worksheets.return_value = []
        mock_db.add_worksheet.side_effect = _add_worksheet

        with patch('backend.dashboard.web_app.get_sheets_client', return_value=mock_db):
            from backend.dashboard.web_app import _ensure_fraud_sheets
            fraud_ws, suspended_ws = _ensure_fraud_sheets()

        # Should have called add_worksheet for both sheets
        titles = [call[1].get('title') or call[0][0]
                  for call in mock_db.add_worksheet.call_args_list]
        assert 'Fraud Alerts' in titles
        assert 'Suspended Cards' in titles

        # Header row appended to each new sheet
        mock_fraud_ws.append_row.assert_called_once_with(FraudDetector.FRAUD_ALERTS_HEADERS)
        mock_suspended_ws.append_row.assert_called_once_with(FraudDetector.SUSPENDED_CARDS_HEADERS)

    def test_uses_existing_sheet_if_present(self):
        mock_db = MagicMock()
        fraud_ws_mock = MagicMock()
        fraud_ws_mock.title = 'Fraud Alerts'
        suspended_ws_mock = MagicMock()
        suspended_ws_mock.title = 'Suspended Cards'

        mock_db.worksheets.return_value = [fraud_ws_mock, suspended_ws_mock]
        mock_db.worksheet.side_effect = lambda t: fraud_ws_mock if t == 'Fraud Alerts' else suspended_ws_mock

        with patch('backend.dashboard.web_app.get_sheets_client', return_value=mock_db):
            from backend.dashboard.web_app import _ensure_fraud_sheets
            fraud_ws, suspended_ws = _ensure_fraud_sheets()

        mock_db.add_worksheet.assert_not_called()
        assert fraud_ws is fraud_ws_mock
