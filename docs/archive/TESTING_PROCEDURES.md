# Testing Procedures

## Overview

Bangko ng Seton uses pytest for automated testing. This document covers how to run tests, write new tests, and interpret results.

## Running Tests

### Run All Tests
```bash
cd L:\Louis\Desktop\BANKONGSETON
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_core_functions.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_core_functions.py::TestCardVerification -v
```

### Run Specific Test Method
```bash
pytest tests/test_core_functions.py::TestCardVerification::test_verify_cards_linked_success -v
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

### Run with Coverage
```bash
# Terminal output
pytest tests/ --cov=backend --cov-report=term-missing

# HTML report
pytest tests/ --cov=backend --cov-report=html
# Then open: coverage_report/index.html
```

---

## Test Structure

### Test Files
```
tests/
├── __init__.py
├── conftest.py                  # Shared fixtures
├── test_core_functions.py       # Core business logic tests
├── test_google_sheets.py        # Google Sheets integration tests
└── test_api.py                  # API endpoint tests (future)
```

### Test Organization
```python
# Group related tests in classes
class TestCardVerification:
    """Test card verification logic"""
    
    def test_verify_cards_linked_success(self):
        """Test successful card linkage verification"""
        # Test implementation
        pass
    
    def test_verify_cards_not_linked(self):
        """Test detection of unlinked cards"""
        pass
```

---

## Test Categories

### Unit Tests
Test isolated functions without external dependencies.

**Markers:** `@pytest.mark.unit`

**Examples:**
- Card UID normalization
- Balance calculations
- Transaction ID generation
- Serial protocol parsing

```python
@pytest.mark.unit
def test_normalize_card_uid():
    """Test UID normalization"""
    from backend.utils import normalize_card_uid
    assert normalize_card_uid('3a2b1c4d') == '3A2B1C4D'
```

### Integration Tests
Test interactions with external systems (mocked).

**Markers:** `@pytest.mark.integration`

**Examples:**
- Google Sheets operations
- Database queries
- Cache operations

```python
@pytest.mark.integration
def test_get_student_by_card(mock_google_sheets):
    """Test retrieving student data"""
    # Test with mocked Google Sheets
    pass
```

### Serial/Hardware Tests
Test Arduino communication (requires hardware).

**Markers:** `@pytest.mark.serial`

**Note:** These tests are skipped by default. Run only when Arduino is connected.

```bash
pytest tests/ -m serial -v
```

---

## Using Fixtures

### Built-in Fixtures

#### mock_google_sheets
Mocks Google Sheets API client.

```python
def test_something(mock_google_sheets):
    users_sheet = mock_google_sheets['users']
    users_sheet.get_all_records.return_value = [...]
```

#### sample_student_data
Returns list of sample student records.

```python
def test_find_student(sample_student_data):
    student = sample_student_data[0]
    assert student['StudentID'] == '2024-001'
```

#### sample_money_account_data
Returns list of sample money account records.

#### sample_transaction_data
Returns list of sample transaction records.

#### test_env_vars
Sets up test environment variables.

```python
def test_config(test_env_vars):
    import os
    assert os.getenv('GOOGLE_SHEETS_ID') == 'test_sheet_id_12345'
```

#### mock_philippines_time
Returns fixed datetime for consistent testing.

---

## Writing New Tests

### 1. Choose Test File
- Core functions → `test_core_functions.py`
- Google Sheets → `test_google_sheets.py`
- New feature → Create new file `test_feature_name.py`

### 2. Create Test Class
```python
class TestNewFeature:
    """Test description"""
    pass
```

### 3. Write Test Methods
```python
def test_feature_works_correctly(self):
    """Test specific behavior"""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output
```

### 4. Use Fixtures
```python
def test_with_fixture(mock_google_sheets, sample_student_data):
    """Test using fixtures"""
    # Fixtures are automatically passed
    pass
```

### 5. Add Markers
```python
@pytest.mark.unit
def test_unit_function(self):
    """Unit test"""
    pass

@pytest.mark.integration
def test_integration_function(self, mock_google_sheets):
    """Integration test"""
    pass
```

---

## Test Guidelines

### DO:
✅ Test one thing per test method  
✅ Use descriptive test names  
✅ Include docstrings explaining what is tested  
✅ Use arrange-act-assert pattern  
✅ Mock external dependencies  
✅ Test both success and failure cases  
✅ Test edge cases (empty input, invalid data)  

### DON'T:
❌ Test framework code (Flask, gspread, etc.)  
❌ Test external APIs directly  
❌ Write tests that depend on specific data in Google Sheets  
❌ Use real serial ports in automated tests  
❌ Make tests dependent on execution order  
❌ Leave failing tests uncommitted  

---

## Interpreting Results

### Success Output
```
tests/test_core_functions.py::test_something PASSED [100%]
=== 50 passed in 2.74s ===
```

### Failure Output
```
tests/test_core_functions.py::test_something FAILED
________________________ test_something _________________________

def test_something():
    result = function()
>   assert result == expected
E   AssertionError: assert 'actual' == 'expected'

tests/test_core_functions.py:25: AssertionError
=== 1 failed, 49 passed in 3.01s ===
```

### Coverage Report
```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
backend/errors.py               120      5    96%   45-49
backend/config_validator.py     180     20    89%   120-140
backend/utils.py                 50      0   100%
-----------------------------------------------------------
TOTAL                           350     25    93%
```

---

## Continuous Integration

### Pre-commit Checks
Before committing code, run:

```bash
# Run all tests
pytest tests/ -v

# Check coverage (aim for 80%+)
pytest tests/ --cov=backend --cov-report=term-missing

# Verify no errors
echo %ERRORLEVEL%  # Should be 0
```

### Automated Testing
Future: Set up GitHub Actions to run tests on every push.

---

## Debugging Tests

### Run with Print Statements
```bash
pytest tests/ -v -s
```
The `-s` flag shows print() output.

### Run with Debugger
```python
def test_something():
    import pdb; pdb.set_trace()
    # Test code
```

### Show Full Traceback
```bash
pytest tests/ -v --tb=long
```

### Stop on First Failure
```bash
pytest tests/ -x
```

---

## Test Maintenance

### When to Update Tests

1. **Bug Fix:**
   - Add test that reproduces bug
   - Fix code
   - Verify test passes

2. **New Feature:**
   - Write tests first (TDD approach)
   - Implement feature
   - Verify tests pass

3. **Refactoring:**
   - Ensure all tests pass before starting
   - Refactor code
   - Tests should still pass without changes

4. **Schema Change:**
   - Update fixtures in `conftest.py`
   - Update related tests
   - Verify all tests pass

---

## Testing Checklist

Before marking Phase 0 complete:
- [ ] All existing tests pass
- [ ] Code coverage ≥ 80%
- [ ] No skipped tests (except hardware tests)
- [ ] No ignored warnings
- [ ] Test documentation is current

---

## Common Issues

### "No module named..." Error
**Fix:** Install test dependencies
```bash
pip install -r requirements-test.txt
```

### Coverage Not Generated
**Fix:** Run from project root
```bash
cd L:\Louis\Desktop\BANKONGSETON
pytest tests/ --cov=backend
```

### Tests Fail Randomly
**Fix:** Tests may have timing issues or dependencies. Review test isolation.

### Slow Test Execution
**Fix:** Mark slow tests with `@pytest.mark.slow` and skip them during development:
```bash
pytest tests/ -m "not slow"
```

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- Project fixtures: `tests/conftest.py`
- Error codes: `docs/ERROR_CODES.md`
