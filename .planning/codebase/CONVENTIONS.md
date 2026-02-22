# Coding Conventions

**Analysis Date:** 2026-02-22

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `api_server.py`, `nfc_payments.py`, `fraud_detection.py`)
- Test files: `test_<module>.py` or `<module>_test.py` (e.g., `test_core_functions.py`, `test_google_sheets.py`)
- Dashboard files: descriptive names in `snake_case` (e.g., `admin_dashboard.py`, `web_app_complete.py`)

**Functions:**
- Module-level functions: `snake_case` (e.g., `get_philippines_time()`, `normalize_card_uid()`, `get_sheets_client()`)
- Private helper functions: `_snake_case` prefix (e.g., `_generate_secure_token()`, `_get_overall_status()`, `_check_google_sheets()`)
- Getter functions: `get_<resource>()` pattern (e.g., `get_logger()`, `get_health_status()`, `get_worksheets()`)
- Boolean checker functions: typically use `is_` or `check_` prefix but may use descriptive name (e.g., `is_expired()`, `verify_pin()`)

**Variables:**
- Instance variables: `snake_case`, with `_` prefix for private (e.g., `self._cache`, `self._stats`, `self._health_monitor`)
- Public attributes: `snake_case` without underscore (e.g., `self.enabled`, `self.token`, `self.created_at`)
- Constants: `UPPERCASE_WITH_UNDERSCORES` for module-level config (e.g., `JWT_SECRET`, `PHILIPPINES_TZ`, `JWT_ALGORITHM`)
- Dictionary keys: lowercase with underscores (e.g., `'requests_total'`, `'error_code'`, `'response_body'`)

**Types/Classes:**
- Class names: `PascalCase` (e.g., `BankoError`, `EmailNotifier`, `HealthMonitor`, `VirtualCard`)
- Enum classes: `PascalCase` (e.g., `ErrorCode`, base `Enum`)
- Type annotations: Standard Python typing (e.g., `Dict[str, Any]`, `Optional[str]`, `List[Dict]`)

## Code Style

**Formatting:**
- No explicit formatter detected (no .prettierrc, .eslintrc, or biome.json)
- Code follows implicit Python conventions: 4-space indentation, blank lines between logical sections
- Line breaks used liberally for readability in docstrings and multi-line configurations

**Linting:**
- No linter configuration found
- Code quality maintained through manual conventions and testing

**Docstring Style:**
- Module-level docstrings: Triple-quoted strings at top of file describing module purpose
- Function docstrings: Formatted with `Args:`, `Returns:`, `Raises:` sections where applicable
- Class docstrings: One-line or multi-line description of class purpose
- Example from `errors.py`:
  ```python
  def setup_logging(log_dir: str = 'logs', log_level: str = 'INFO'):
      """
      Configure logging for the application

      Args:
          log_dir: Directory to store log files
          log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      """
  ```

## Import Organization

**Order:**
1. Standard library imports (`import os`, `import sys`, `from datetime import ...`)
2. Third-party imports (`import flask`, `import gspread`, `import pytz`)
3. Local imports (`from backend.errors import ...` or `from errors import ...`)

**Path Aliases:**
- Relative imports use try/except pattern for flexibility (can be imported from different locations)
- Example from `nfc_payments.py`:
  ```python
  try:
      from backend.errors import BankoError, ErrorCode, get_logger
  except ImportError:
      from errors import BankoError, ErrorCode, get_logger
  ```

**Environment Configuration:**
- Module constants defined near imports (e.g., `PHILIPPINES_TZ = pytz.timezone('Asia/Manila')`)
- Environment variables loaded with `load_dotenv()` early in main modules
- Sensitive configs never hardcoded; always use environment variables via `os.getenv()`

## Error Handling

**Patterns:**
- Custom exception hierarchy: `BankoError` base exception with `ErrorCode` enum for categorization
- Error conversion functions: `handle_sheets_error()`, `handle_serial_error()` convert external exceptions to `BankoError`
- Error details captured in dict format: `{'original_error': str(error)}`
- All errors include `recoverable` flag to indicate if operation can be retried
- HTTP responses use `create_error_response()` to format errors as JSON
- File: `backend/errors.py` - centralized error handling and logging

**Common patterns:**
- Try/except blocks with specific error types (e.g., `jwt.ExpiredSignatureError`, `jwt.InvalidTokenError`)
- Defensive programming with fallback paths (e.g., credential path lookup with backward compatibility fallback)
- Logging errors with context before returning error responses

## Logging

**Framework:** Python `logging` module

**Patterns:**
- Logger obtained via `get_logger()` function (returns module logger 'bangko')
- All major operations logged with level: `INFO`, `DEBUG`, `WARNING`, `ERROR`, `CRITICAL`
- Error logging includes exception info: `exc_info=True`
- Contextual data passed via `extra={}` parameter in log calls
- Example from `health.py`:
  ```python
  self.logger.error(f"Error checking system resources: {e}")
  self.logger.warning("System marked as DOWN")
  ```

**Setup:**
- Logging configured via `setup_logging()` in `errors.py`
- Two handlers: file (all levels) + console (INFO+)
- Log files stored in `logs/` directory with daily rotation pattern: `bangko_YYYY-MM-DD.log`
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Comments

**When to Comment:**
- Complex algorithmic logic requiring explanation
- Non-obvious workarounds or special cases
- Performance-critical sections explaining optimization rationale
- Configuration sections explaining why specific values are used

**JSDoc/TSDoc:**
- Not used (Python project)
- Docstrings follow NumPy-style format with Args/Returns/Raises sections

**Comment Examples:**
- Inline comments used sparingly for code clarity
- Header comments for major sections (e.g., `# JWT Configuration`, `# Google Sheets Setup`)
- TODOs/FIXMEs may appear in development (check code for any existing ones)

## Function Design

**Size:** Functions generally 20-50 lines, with complex methods up to 100+ lines for state management

**Parameters:**
- Explicit parameters preferred over **kwargs
- Type annotations used: `def func(param: Type) -> ReturnType:`
- Default values for optional parameters (e.g., `default_ttl: int = 30`)
- Complex parameters documented in docstring

**Return Values:**
- Explicit return statements required
- Dictionary returns common for structured data
- Tuple returns for multiple values: `Tuple[status, value]`
- Optional returns explicitly typed: `Optional[T]`
- None returned for missing/error cases (with proper exception handling in callers)

**Example from `cache.py`:**
```python
def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
    """Get value from cache, optionally returning stale data"""
```

## Module Design

**Exports:**
- Classes defined for major concepts (e.g., `HealthMonitor`, `TTLCache`, `VirtualCard`)
- Module-level singleton functions for convenience (e.g., `get_health_monitor()`, `get_logger()`)
- Factory functions for creating instances with defaults (e.g., `get_sheets_client()`)

**Barrel Files:**
- Not used in this codebase
- Each module imports directly what it needs

**Module Responsibilities:**
- Single responsibility principle observed: `cache.py` handles caching, `errors.py` handles errors, etc.
- Cross-module dependencies via imports (e.g., `health.py` imports from `cache.py` and `resilience.py`)
- Circular dependency avoidance through careful module organization

## Type Annotations

**Usage:**
- Type hints used consistently in function signatures
- Import types from `typing` module: `Dict`, `List`, `Optional`, `Any`, `Tuple`, `Callable`
- Complex types built from primitives (e.g., `Dict[str, Any]` for flexible dictionaries)
- Class type hints in `__init__` methods

**Examples from codebase:**
- `def setup_logging(log_dir: str = 'logs', log_level: str = 'INFO'):`
- `def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:`
- `def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):`

---

*Convention analysis: 2026-02-22*
