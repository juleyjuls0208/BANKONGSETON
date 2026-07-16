"""
Pytest fixtures and test configuration
"""
import pytest
import os
import sys
import jwt
from unittest.mock import Mock, MagicMock, patch
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()


def pytest_configure(config):
    """Normalize wrapped -k expressions passed by external verifiers.

    Some wrappers pass the keyword expression as a literal quoted string,
    e.g. ``-k '"student_budget"'``. Pytest treats that as invalid syntax.
    Strip one matching pair of outer quotes so selection remains valid.
    """
    keyword = getattr(config.option, "keyword", None)
    if not isinstance(keyword, str):
        return

    stripped = keyword.strip()
    if len(stripped) < 2:
        return

    if stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        config.option.keyword = stripped[1:-1]

@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets client for testing without API calls"""
    mock_client = MagicMock()
    mock_spreadsheet = MagicMock()
    mock_client.open_by_key.return_value = mock_spreadsheet
    
    # Mock worksheets
    users_sheet = MagicMock()
    money_accounts_sheet = MagicMock()
    transactions_sheet = MagicMock()
    lost_cards_sheet = MagicMock()
    
    def get_worksheet(name):
        sheets_map = {
            'Users': users_sheet,
            'Money Accounts': money_accounts_sheet,
            'Transactions Log': transactions_sheet,
            'Lost Card Reports': lost_cards_sheet
        }
        return sheets_map.get(name)
    
    mock_spreadsheet.worksheet.side_effect = get_worksheet
    
    return {
        'client': mock_client,
        'spreadsheet': mock_spreadsheet,
        'users': users_sheet,
        'money_accounts': money_accounts_sheet,
        'transactions': transactions_sheet,
        'lost_cards': lost_cards_sheet
    }

@pytest.fixture
def sample_student_data():
    """Sample student data for testing"""
    return [
        {
            'StudentID': '2024-001',
            'Name': 'Louis Julian Adriatico',
            'IDCardNumber': '3A2B1C4D',
            'MoneyCardNumber': '5F6E7D8C',
            'Status': 'Active',
            'ParentEmail': 'parent@email.com',
            'DateRegistered': '2026-02-02 10:30:45'
        },
        {
            'StudentID': '2024-002',
            'Name': 'Maria Santos',
            'IDCardNumber': '1F2E3D4C',
            'MoneyCardNumber': '',
            'Status': 'Active',
            'ParentEmail': 'maria@email.com',
            'DateRegistered': '2026-02-02 11:00:00'
        }
    ]

@pytest.fixture
def sample_money_account_data():
    """Sample money account data for testing"""
    return [
        {
            'MoneyCardNumber': '5F6E7D8C',
            'LinkedIDCard': '3A2B1C4D',
            'Balance': '500.00',
            'Status': 'Active',
            'LastUpdated': '2026-02-02 10:30:45',
            'TotalLoaded': '1000.00'
        }
    ]

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return [
        {
            'TransactionID': 'TXN-20260202103045',
            'Timestamp': '2026-02-02 10:30:45',
            'StudentID': '2024-001',
            'MoneyCardNumber': '5F6E7D8C',
            'TransactionType': 'Load',
            'Amount': '100.00',
            'BalanceBefore': '400.00',
            'BalanceAfter': '500.00',
            'Status': 'Completed',
            'ErrorMessage': ''
        }
    ]

@pytest.fixture
def mock_serial_port():
    """Mock serial port for Arduino communication testing"""
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    mock_serial.read_until.return_value = b'<CARD|3A2B1C4D>\n'
    return mock_serial

@pytest.fixture
def test_env_vars(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv('GOOGLE_SHEETS_ID', 'test_sheet_id_12345')
    monkeypatch.setenv('FLASK_SECRET_KEY', 'test_secret_key')
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'testpass')
    monkeypatch.setenv('SERIAL_PORT', 'COM3')
    monkeypatch.setenv('ADMIN_PORT', 'COM4')
    monkeypatch.setenv('BAUD_RATE', '9600')

@pytest.fixture
def mock_philippines_time():
    """Mock Philippine timezone for consistent testing"""
    from datetime import datetime
    import pytz
    tz = pytz.timezone('Asia/Manila')
    return datetime(2026, 2, 2, 10, 30, 45, tzinfo=tz)


# ---------------------------------------------------------------------------
# S04 — Critical Path Unit Tests: shared Flask test infrastructure
# ---------------------------------------------------------------------------

# Module-level reference to the imported admin_dashboard — set by flask_app fixture.
# Other fixtures reference this to replace adm.db per-test.
_adm = None


def _make_cashier_token(username: str, role: str) -> str:
    """Return a signed JWT readable by cashier_routes' @jwt_required decorator.

    Uses the same secret and algorithm as cashier_routes.py:
        JWT_SECRET = os.getenv('JWT_SECRET', 'bangko-jwt-secret-2026')
        JWT_ALGORITHM = 'HS256'
    """
    secret = os.getenv('JWT_SECRET', 'bangko-jwt-secret-2026')
    payload = {'username': username, 'role': role}
    return jwt.encode(payload, secret, algorithm='HS256')


def _set_pending(client, items: list, total: float) -> None:
    """Seed pending_transaction in Flask session via session_transaction().

    Args:
        client: Flask test client.
        items: list of item dicts (e.g. [{'name': 'Item', 'price': 10.0, 'qty': 1}]).
        total: numeric total of the transaction.
    """
    with client.session_transaction() as sess:
        sess['pending_transaction'] = {'items': items, 'total': total}


@pytest.fixture(scope='module')
def flask_app():
    """Module-scoped fixture: Flask test client with mocked Sheets.

    Sets required env vars and starts gspread patches BEFORE importing
    admin_dashboard (its module-level db = get_sheets_client() runs at import
    time).  Also registers sys.modules['admin_dashboard'] so that cashier_routes'
    inline `from admin_dashboard import get_sheets_client` resolves to the same
    already-mocked module object.

    Yields:
        (Flask app, mock_spreadsheet) tuple so tests can destructure both.
    """
    global _adm

    # Step 1 — env vars required by admin_dashboard startup guards
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-s04'
    os.environ['GOOGLE_SHEETS_ID'] = 'fake-sheet-id-s04'
    os.environ['WEB_CONCURRENCY'] = '1'
    os.environ['ADMIN_USERNAME'] = 'admin'
    os.environ['ADMIN_PASSWORD'] = 'adminpass'
    os.environ['FINANCE_USERNAME'] = 'finance'
    os.environ['FINANCE_PASSWORD'] = 'financepass'

    # Step 2 — build mock spreadsheet used by all module-level tests
    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheets.return_value = []
    mock_spreadsheet.add_worksheet.return_value = MagicMock()
    mock_spreadsheet.worksheet.return_value = MagicMock()

    # Step 2b — add backend/dashboard to sys.path so cashier blueprint import succeeds
    _dashboard_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'dashboard')
    if _dashboard_dir not in sys.path:
        sys.path.insert(0, _dashboard_dir)

    # Step 3 — start patches before import so module-level db = get_sheets_client() uses mocks
    creds_patch = patch(
        'google.oauth2.service_account.Credentials.from_service_account_file',
        return_value=MagicMock()
    )
    gspread_patch = patch('gspread.authorize', return_value=MagicMock(
        open_by_key=MagicMock(return_value=mock_spreadsheet)
    ))

    creds_patch.start()
    gspread_patch.start()

    # Step 4 — import the deployed dashboard (web_app) — admin_dashboard.py was
    # removed; its Arduino/card-tap logic now lives in registration_app.py (on-prem).
    # web_app is the production cloud dashboard and exposes the same app/db/get_sheets_client
    # interface the fixtures expect.
    try:
        import backend.dashboard.web_app as adm  # noqa: F401
    except Exception:
        pass  # may already be cached; the second import below retrieves the cached copy

    import backend.dashboard.web_app as adm

    # Step 5 — stop patches (imports complete; patches no longer needed at runtime)
    creds_patch.stop()
    gspread_patch.stop()

    # Step 6 — replace live db references on the already-imported module
    adm.db = mock_spreadsheet
    adm.get_sheets_client = lambda: mock_spreadsheet

    # Step 7 — register under short name so cashier_routes' inline import resolves here
    sys.modules['admin_dashboard'] = adm

    # Step 8 — stash module reference for function-scoped db fixture
    _adm = adm

    # Step 9 — configure Flask for testing
    adm.app.config['TESTING'] = True
    adm.app.config['WTF_CSRF_ENABLED'] = False

    yield adm.app, mock_spreadsheet


@pytest.fixture
def db(flask_app):
    """Function-scoped fixture: fresh mock spreadsheet per test.

    Prevents worksheet mock state (call counts, return_value changes) from
    leaking between tests.  Reassigns adm.db and adm.get_sheets_client so
    every request handler sees the fresh mock.
    """
    fresh = MagicMock()
    fresh.worksheets.return_value = []
    fresh.add_worksheet.return_value = MagicMock()
    fresh.worksheet.return_value = MagicMock()

    if _adm is not None:
        _adm.db = fresh
        _adm.get_sheets_client = lambda: fresh

    yield fresh

    # Restore a generic mock after test so module is not left in a broken state
    if _adm is not None:
        _adm.db = MagicMock()
        _adm.get_sheets_client = lambda: _adm.db


@pytest.fixture
def admin_client(flask_app):
    """Authenticated Flask test client logged in as admin."""
    app, _ = flask_app
    client = app.test_client()
    client.post(
        '/login',
        json={
            'username': os.environ.get('ADMIN_USERNAME', 'admin'),
            'password': os.environ.get('ADMIN_PASSWORD', 'adminpass'),
        }
    )
    return client


@pytest.fixture
def finance_client(flask_app):
    """Authenticated Flask test client logged in as finance user."""
    app, _ = flask_app
    client = app.test_client()
    client.post(
        '/login',
        json={
            'username': os.environ.get('FINANCE_USERNAME', 'finance'),
            'password': os.environ.get('FINANCE_PASSWORD', 'financepass'),
        }
    )
    return client
