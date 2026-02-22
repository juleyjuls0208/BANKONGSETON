# Codebase Structure

**Analysis Date:** 2026-02-22

## Directory Layout

```
BANKONGSETON/
├── backend/                         # Python Flask backend (main application)
│   ├── api/
│   │   └── api_server.py           # Mobile API REST endpoints
│   ├── dashboard/
│   │   ├── admin_dashboard.py       # Admin web dashboard (with Arduino support)
│   │   ├── web_app_complete.py      # Admin web dashboard (web-only, no Arduino)
│   │   ├── wsgi.py                  # WSGI entry point for production
│   │   ├── arduino_bridge.py        # Serial communication with Arduino
│   │   ├── cashier/
│   │   │   ├── cashier_routes.py    # Cashier POS blueprint
│   │   │   ├── static/              # Cashier static assets (CSS, JS)
│   │   │   └── templates/           # Cashier HTML templates
│   │   ├── static/                  # Dashboard static assets (CSS, JS, icons)
│   │   ├── templates/               # Dashboard HTML templates
│   │   └── generate_icons.py        # PWA icon generation utility
│   ├── services/
│   │   └── email_service.py         # Email utility service
│   ├── data/                        # Data migration and fixtures
│   ├── analytics.py                 # Phase 3: Transaction analytics engine
│   ├── cache.py                     # TTL cache with LRU eviction
│   ├── config_validator.py          # Configuration validation at startup
│   ├── connection_pool.py           # Google Sheets connection pooling
│   ├── errors.py                    # Centralized error handling & logging
│   ├── exports.py                   # Phase 3: CSV/Excel export functionality
│   ├── fraud_detection.py           # Phase 4: Fraud detection system
│   ├── health.py                    # Health monitoring and status
│   ├── migrate_transactions.py      # Data migration utility
│   ├── nfc_payments.py              # Phase 4: NFC phone payments (HCE)
│   ├── notifications.py             # Phase 3: Email notifications
│   ├── resilience.py                # Retry logic, rate limiting, write queue
│   ├── sync.py                      # Phase 2: Multi-station synchronization
│   └── __pycache__/                 # Python bytecode (generated)
├── config/                          # Configuration files
│   └── credentials.json             # Google Sheets API credentials (not in git)
├── mobile/                          # Mobile app projects
│   ├── android/                     # Android app source
│   ├── BankongSetonApp/             # Flutter/Kotlin app variant
│   └── student_app_v2/              # Student app version 2
├── tests/                           # Test suite
│   ├── conftest.py                  # pytest configuration and fixtures
│   ├── test_core_functions.py       # Phase 0-1 core feature tests
│   ├── test_google_sheets.py        # Google Sheets integration tests
│   ├── test_phase1_features.py      # Phase 1 feature tests
│   ├── test_phase2_pwa.py           # Phase 2 PWA tests
│   ├── test_phase3_analytics.py     # Phase 3 analytics tests
│   ├── test_phase4_scale.py         # Phase 4 scale tests
│   └── __init__.py
├── docs/                            # Documentation
├── logs/                            # Log files (generated at runtime)
├── coverage_report/                 # Test coverage reports (generated)
├── .planning/                       # GSD planning documents
│   └── codebase/                    # Architecture and structure analysis
├── .vscode/                         # VS Code settings
├── .env.example                     # Environment variables template
├── README.md                        # Project documentation
├── requirements.txt                 # Python dependencies
└── .git/                            # Git repository
```

## Directory Purposes

**backend/:**
- Purpose: Main Python Flask application serving API, dashboard, and cashier interface
- Contains: All business logic, database integration, hardware control
- Key files: `api_server.py` (API), `admin_dashboard.py` (web UI)

**backend/api/:**
- Purpose: REST API for mobile and external clients
- Contains: JWT auth, student/card endpoints, balance queries, transaction creation
- Key files: `api_server.py` (Flask app with all API routes)

**backend/dashboard/:**
- Purpose: Web-based admin and finance interface
- Contains: Flask templates, dashboards, cashier POS system, Arduino integration
- Key files: `admin_dashboard.py` (main), `web_app_complete.py` (alternative)

**backend/dashboard/cashier/:**
- Purpose: Point-of-sale system for transaction processing
- Contains: Cashier blueprint, card reader UI, transaction flow
- Key files: `cashier_routes.py` (blueprint definition)

**backend/services/:**
- Purpose: Reusable service utilities
- Contains: Email service helper functions
- Key files: `email_service.py`

**backend/data/:**
- Purpose: Data migrations, fixtures, sample data
- Contains: Migration scripts and test data generators
- Key files: Various migration and seeding scripts

**config/:**
- Purpose: Configuration storage
- Contains: Google Sheets API credentials (credentials.json - NOT in git)
- Key files: None committed; credentials added at deployment

**mobile/:**
- Purpose: Android/Kotlin mobile application for students
- Contains: App source code, resources, build artifacts
- Key files: Android app manifest, activities, UI components

**tests/:**
- Purpose: Automated test suite
- Contains: Unit, integration, and end-to-end tests (170 tests total)
- Key files: test_*.py modules organized by feature phase

**logs/:**
- Purpose: Runtime application logs
- Contains: Application execution logs (generated, not committed)
- Key files: None; created during runtime

**docs/:**
- Purpose: User and developer documentation
- Contains: Setup guides, API documentation, troubleshooting
- Key files: Google Sheets setup, hardware guide, API reference

## Key File Locations

**Entry Points:**
- `backend/api/api_server.py`: Mobile API (starts Flask server on port 5001)
- `backend/dashboard/admin_dashboard.py`: Admin dashboard with Arduino support (port 5003)
- `backend/dashboard/web_app_complete.py`: Web-only dashboard without Arduino (port 5003)
- `backend/dashboard/wsgi.py`: Production WSGI entry point
- `backend/config_validator.py`: Configuration startup validation

**Configuration:**
- `.env`: Environment variables (API keys, credentials paths, passwords)
- `.env.example`: Template for required environment variables
- `config/credentials.json`: Google Sheets service account credentials (locally only)
- `requirements.txt`: Python package dependencies

**Core Logic:**
- `backend/errors.py`: Error codes (100+ specific codes), BankoError exception class
- `backend/cache.py`: TTL cache implementation with LRU eviction
- `backend/resilience.py`: Retry decorator, exponential backoff, rate limiting
- `backend/sync.py`: Transaction ID generation, multi-station locking
- `backend/health.py`: System health monitoring

**Feature Modules:**
- `backend/fraud_detection.py`: Fraud detection engine (Phase 4)
- `backend/nfc_payments.py`: NFC phone payments via HCE (Phase 4)
- `backend/analytics.py`: Spending analysis and reporting (Phase 3)
- `backend/notifications.py`: Email notification system (Phase 3)
- `backend/exports.py`: CSV/Excel data export (Phase 3)

**Testing:**
- `tests/conftest.py`: pytest fixtures and setup
- `tests/test_phase1_features.py`: Dual-card, RFID, transactions
- `tests/test_phase2_pwa.py`: Dashboard PWA features
- `tests/test_phase3_analytics.py`: Analytics and exports
- `tests/test_phase4_scale.py`: Fraud detection, NFC, sync

## Naming Conventions

**Files:**
- Module files: `lowercase_with_underscores.py` (e.g., `fraud_detection.py`)
- Entry points: Named descriptively (e.g., `api_server.py`, `admin_dashboard.py`)
- Test files: `test_*.py` prefix (e.g., `test_phase1_features.py`)
- Blueprints: Descriptive names with `_routes.py` suffix (e.g., `cashier_routes.py`)
- Static assets: Lowercase in appropriate subdirs (css/, js/, icons/)

**Directories:**
- Feature directories: `lowercase_with_underscores/` (e.g., `backend/`, `mobile/`)
- Grouped modules: Named by domain (api/, dashboard/, services/)
- Generated/runtime: Preceded by underscore or descriptive (\_\_pycache\_\_, logs/, coverage_report/)
- Static assets: Standard names (static/, templates/)

**Python Classes:**
- Pattern: PascalCase (e.g., BankoError, TransactionIDGenerator, VirtualCard)
- Error classes: Suffix with "Error" (e.g., BankoError)
- Configuration classes: Suffix with "Config" (e.g., RetryConfig)
- Detector/Manager classes: Suffix with type (e.g., FraudDetector, HealthMonitor)

**Python Functions:**
- Pattern: lowercase_with_underscores (e.g., get_philippines_time, with_retry)
- Decorators: verb_adjective or adjective_noun (e.g., jwt_required, with_retry)
- Boolean getters: Prefix with "is_" or "get_" (e.g., is_expired, get_health_status)

**Constants:**
- Pattern: UPPERCASE_WITH_UNDERSCORES (e.g., JWT_SECRET, PHILIPPINES_TZ)
- Environment vars: Uppercase (e.g., GOOGLE_SHEETS_ID, FLASK_SECRET_KEY)

**Routes:**
- API routes: `/api/*` prefix (e.g., `/api/login`, `/api/balance`)
- Dashboard routes: `/` root with HTML endpoints
- Cashier routes: `/cashier/*` prefix (e.g., `/cashier/login`, `/cashier/process-payment`)

## Where to Add New Code

**New Feature:**
- Primary code: Create module in `backend/` at root level (e.g., `backend/new_feature.py`)
- Service logic: If complex, create class-based structure in same module
- Tests: Add test file `tests/test_new_feature.py` with comprehensive coverage
- Entry points: Register routes in appropriate blueprint/server (api or dashboard)

**New Component/Module:**
- Implementation: Create `backend/new_component.py` for single-file or `backend/new_component/` directory for multi-file
- Related logic: Keep tightly coupled classes together in same module
- Public API: Use explicit imports/exports at module level
- Tests: Corresponding test file with class/function stubs if needed

**Database-like Operations:**
- Google Sheets interaction: Use gspread client via `backend/api/api_server.py::get_sheets_client()`
- Caching: Wrap with `backend/cache.py::@get_cached` or TTLCache methods
- Retries: Decorate calls with `backend/resilience.py::@with_retry(RetryConfig())`
- Error handling: Raise `BankoError` with appropriate ErrorCode from `backend/errors.py::ErrorCode`

**UI Routes & Templates:**
- Dashboard routes: Add to `backend/dashboard/admin_dashboard.py` (or web_app_complete.py)
- Cashier routes: Add to `backend/dashboard/cashier/cashier_routes.py` Blueprint
- HTML templates: Place in appropriate `templates/` subdirectory
- Static assets: Place in `static/` subdirectory (css/, js/, icons/)
- Form processing: Use @app.route (POST) with JSON request handling

**Utilities & Helpers:**
- Shared helpers: `backend/services/` for reusable components
- Internal utilities: Module-level functions in relevant `backend/module.py`
- Configuration helpers: Add validation to `backend/config_validator.py`
- Time operations: Use `get_philippines_time()` helper from respective module

## Special Directories

**backend/__pycache__/:**
- Purpose: Python compiled bytecode (generated)
- Generated: Yes (created by Python)
- Committed: No (excluded via .gitignore)
- Management: Auto-managed; safe to delete for cleanup

**logs/:**
- Purpose: Application runtime logs
- Generated: Yes (created during application execution)
- Committed: No (excluded via .gitignore)
- Management: Rotated automatically, old files safe to delete

**coverage_report/:**
- Purpose: Test coverage analysis HTML report (generated)
- Generated: Yes (created by pytest-cov)
- Committed: No (excluded via .gitignore)
- Management: Regenerated by test runs; safe to delete

**config/credentials.json:**
- Purpose: Google Sheets service account JSON key
- Generated: No (manually placed)
- Committed: No (excluded via .gitignore for security)
- Management: Added locally; never committed to repository

**mobile/ (build artifacts):**
- Purpose: Android build intermediates and outputs
- Generated: Yes (created by gradle)
- Committed: No (build/ excluded via .gitignore)
- Management: Auto-cleaned; regenerated on rebuild

## Import Patterns

**Standard imports (always available):**
```python
from flask import Flask, jsonify, request
import gspread
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
```

**Project imports (relative):**
```python
# From same directory
from .errors import BankoError, ErrorCode

# From parent directory
from errors import BankoError, get_logger
```

**Conditional imports (with fallback):**
```python
# In dashboard/admin_dashboard.py
try:
    from cache import get_cache_stats
    from resilience import with_retry
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
```

**Module path setup (for backend access from subdirs):**
```python
# In cashier_routes.py or dashboard modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from errors import BankoError
```

---

*Structure analysis: 2026-02-22*
