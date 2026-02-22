# Testing Patterns

**Analysis Date:** 2026-02-22

## Test Framework

**Runner:**
- pytest 7.4.0+
- Config: `pytest.ini`

**Assertion Library:**
- Python built-in `assert` statements

**Run Commands:**
```bash
pytest                          # Run all tests in tests/ directory
pytest -v                       # Verbose output
pytest -m unit                  # Run only unit tests
pytest -m integration           # Run only integration tests
pytest --cov=backend            # Run with coverage report
pytest --cov-report=html        # Generate HTML coverage report
```

**Configuration Details from `pytest.ini`:**
- Test discovery: `test_*.py` and `*_test.py` files
- Test classes: `Test*` pattern
- Test functions: `test_*` pattern
- Test paths: searches in `tests/` directory
- Default options: `-v --tb=short --strict-markers --disable-warnings --color=yes`
- Coverage: `--cov=backend --cov-report=term-missing --cov-report=html:coverage_report --cov-branch`
- Markers defined: `unit`, `integration`, `slow`, `serial`, `sheets`

## Test File Organization

**Location:**
- Separate directory: `tests/` folder (not co-located with source)
- Additional ad-hoc tests in backend for quick validation: `backend/test_phase1.py`, `backend/test_phase3.py`

**Naming:**
- Pattern: `test_<feature>.py` (e.g., `test_core_functions.py`, `test_google_sheets.py`, `test_phase1_features.py`)
- Class-based tests grouped by feature/area

**Structure:**
```
tests/
├── conftest.py                   # Shared fixtures
├── test_core_functions.py        # Core utility tests
├── test_google_sheets.py         # Google Sheets integration
├── test_phase1_features.py       # Phase 1: Cache, resilience, health
├── test_phase2_pwa.py            # Phase 2: PWA features
├── test_phase3_analytics.py      # Phase 3: Analytics and exports
└── test_phase4_scale.py          # Phase 4: Scaling tests
```

## Test Structure

**Suite Organization:**
- Classes group related tests by feature/component: `class TestCardVerification:`, `class TestGoogleSheetsConnection:`
- Docstrings on both classes and test methods document intent
- Test class names follow `Test<Feature>` pattern

**Example structure from `test_core_functions.py`:**
```python
"""
Unit tests for core utility functions
"""
import pytest
from datetime import datetime
import pytz


class TestCardUIDNormalization:
    """Test card UID normalization and validation"""

    def test_normalize_card_uid_uppercase(self):
        """Test UID is converted to uppercase"""
        def normalize_card_uid(uid):
            return str(uid).upper().strip()

        assert normalize_card_uid('3a2b1c4d') == '3A2B1C4D'
        assert normalize_card_uid('abcdef12') == 'ABCDEF12'
```

**Patterns:**
- Setup: Via pytest fixtures (centralized in `conftest.py`)
- Teardown: Implicit (fixtures cleaned up by pytest)
- Assertions: Simple `assert` statements with expected == actual pattern

## Fixtures

**Centralized Fixtures (`tests/conftest.py`):**

All shared test data fixtures defined in conftest.py:

- **`mock_google_sheets`** - Mocked Google Sheets client and worksheets
  - Returns dict with `'client'`, `'spreadsheet'`, `'users'`, `'money_accounts'`, `'transactions'`, `'lost_cards'`
  - All sheets are MagicMock objects with configured side_effects

- **`sample_student_data`** - List of student records with StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered

- **`sample_money_account_data`** - List of money account records with MoneyCardNumber, LinkedIDCard, Balance, Status, LastUpdated, TotalLoaded

- **`sample_transaction_data`** - List of transaction records with TransactionID, Timestamp, StudentID, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ErrorMessage

- **`mock_serial_port`** - Mocked serial port for Arduino testing
  - Configured with `is_open = True`, `in_waiting = 0`, `read_until()` returns sample card UID

- **`test_env_vars`** - pytest fixture using monkeypatch to set environment variables
  - Sets: `GOOGLE_SHEETS_ID`, `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SERIAL_PORT`, `ADMIN_PORT`, `BAUD_RATE`

- **`mock_philippines_time`** - Mocked Philippine timezone datetime for consistent testing
  - Returns datetime object with Asia/Manila timezone

**Usage Pattern:**
```python
def test_verify_cards_linked_success(self, sample_student_data, sample_money_account_data):
    """Test successful card linkage verification"""
    student = sample_student_data[0]
    money_account = sample_money_account_data[0]

    assert student['IDCardNumber'] == money_account['LinkedIDCard']
    assert student['MoneyCardNumber'] == money_account['MoneyCardNumber']
```

## Mocking

**Framework:** Python `unittest.mock` module with MagicMock

**Patterns:**
- Mocks created via `MagicMock()` for flexible object mocking
- `Mock()` for simpler cases with specific method configuration
- `side_effect` used to configure method behavior (e.g., return value, raise exception, call sequence)

**Example from `test_google_sheets.py`:**
```python
def test_retry_on_connection_error(self, mock_google_sheets):
    """Test retry logic activates on connection error"""
    spreadsheet = mock_google_sheets['spreadsheet']

    # Simulate failure then success
    spreadsheet.worksheet.side_effect = [
        Exception("Connection timeout"),
        mock_google_sheets['users']
    ]
```

**What to Mock:**
- External services: Google Sheets API client, SMTP server, Serial ports
- Database connections and queries
- Date/time (use `freezegun` for time-based tests, or mock `datetime.now()`)

**What NOT to Mock:**
- Core utility functions that are simple and deterministic
- Data transformation/validation logic
- Error handling code paths

**Mock Cleanup:**
- Automatic via pytest fixtures - no explicit cleanup needed
- Monkeypatch reverts automatically after test

## Test Dependencies

**From `requirements-test.txt`:**
```
pytest>=7.4.0              # Test runner
pytest-cov>=4.1.0          # Code coverage
pytest-mock>=3.11.1        # Mocking utilities
pytest-flask>=1.2.0        # Flask app testing
pytest-asyncio>=0.21.0     # Async test support

responses>=0.23.1          # Mock HTTP requests
freezegun>=1.2.2           # Mock datetime/time
faker>=19.2.0              # Generate fake test data
```

## Coverage

**Requirements:** Enabled in pytest configuration but no explicit target set

**View Coverage:**
```bash
pytest --cov=backend --cov-report=html:coverage_report
# Opens browser to coverage_report/index.html
```

**Coverage Configuration from `pytest.ini`:**
- Source: `backend/` directory
- Omit: tests, venv, migrations, wsgi.py
- Precision: 2 decimal places
- Branch coverage enabled: `--cov-branch`
- Skip empty files: `skip_empty = True`

## Test Types

**Unit Tests:**
- Scope: Single function or class method in isolation
- Approach: Input validation, normalization logic, calculations
- Example from `test_core_functions.py`:
  ```python
  def test_normalize_card_uid_uppercase(self):
      """Test UID is converted to uppercase"""
      def normalize_card_uid(uid):
          return str(uid).upper().strip()
      assert normalize_card_uid('3a2b1c4d') == '3A2B1C4D'
  ```
- Marked with: `@pytest.mark.unit`

**Integration Tests:**
- Scope: Multiple components working together (with mocked external services)
- Approach: Test workflows like "find student → get balance → verify card linkage"
- Example from `test_google_sheets.py`:
  ```python
  @pytest.mark.integration
  class TestGoogleSheetsConnection:
      def test_sheets_client_initialization(self, mock_google_sheets, test_env_vars):
          client = mock_google_sheets['client']
          assert client is not None
  ```
- Marked with: `@pytest.mark.integration`

**Specialized Markers:**
- `@pytest.mark.slow` - Tests that take significant time
- `@pytest.mark.serial` - Tests requiring actual Arduino hardware (skip in CI)
- `@pytest.mark.sheets` - Tests requiring Google Sheets connectivity

**E2E Tests:**
- Not explicitly separated in this codebase
- Ad-hoc validation scripts: `backend/test_phase1.py`, `backend/test_phase3.py`

## Common Patterns

**Fixture Injection:**
```python
def test_cache_stores_and_retrieves_data(self):
    """Test basic cache set/get"""
    from backend.cache import TTLCache

    cache = TTLCache(default_ttl=60)
    cache.set('test_key', 'test_value')

    result = cache.get('test_key')
    assert result == 'test_value'
```

**Testing with Imported Fixtures:**
```python
def test_verify_cards_linked_success(self, sample_student_data, sample_money_account_data):
    """Test successful card linkage verification"""
    student = sample_student_data[0]
    money_account = sample_money_account_data[0]

    assert student['IDCardNumber'] == money_account['LinkedIDCard']
```

**Error Testing:**
- Verify exception is raised: `with pytest.raises(Exception):`
- Check exception message matches expectation
- Example from `test_google_sheets.py`:
  ```python
  def test_max_retries_exceeded(self, mock_google_sheets):
      """Test max retries limit is respected"""
      spreadsheet = mock_google_sheets['spreadsheet']
      spreadsheet.worksheet.side_effect = Exception("Connection failed")

      with pytest.raises(Exception):
          spreadsheet.worksheet('Users')
  ```

**Time-based Testing:**
- Use mocked Philippine timezone: `mock_philippines_time` fixture
- For time progression: `time.sleep()` in TTL tests
- For date ranges: create fixtures with different dates (shown in `test_phase3_analytics.py`)

**Sample Data Fixtures:**
- Student data includes: StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered
- Transaction data includes: TransactionID, Timestamp, StudentID, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ErrorMessage
- Money account data includes: MoneyCardNumber, LinkedIDCard, Balance, Status, LastUpdated, TotalLoaded

---

*Testing analysis: 2026-02-22*
