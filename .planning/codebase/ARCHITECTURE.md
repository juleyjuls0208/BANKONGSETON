# Architecture

**Analysis Date:** 2026-02-22

## Pattern Overview

**Overall:** Layered service-oriented architecture with Flask REST API backend, Google Sheets as persistent storage, and multiple client interfaces (web dashboard, mobile app, Arduino hardware integration).

**Key Characteristics:**
- **Multi-layer separation**: API layer, service layer, persistence layer, and presentation layer
- **Google Sheets-centric**: Uses Google Sheets as database; no traditional SQL database
- **Resilience-first design**: Retry logic, caching, connection pooling, and graceful degradation
- **Hardware integration**: Arduino + RFID card reader for cashier transactions
- **Real-time communication**: WebSocket support via Flask-SocketIO for live updates
- **Role-based access control**: Admin, Finance, and Cashier roles with JWT authentication

## Layers

**API Layer (HTTP/REST):**
- Purpose: Handle HTTP requests from mobile, web, and hardware clients
- Location: `backend/api/api_server.py`
- Contains: Flask route handlers, JWT token generation/verification, CORS configuration
- Depends on: Google Sheets client, error handling (BankoError), utilities
- Used by: Android app, external integrations

**Presentation Layer (Web Dashboard):**
- Purpose: Web UI for admin and finance users to manage system
- Location: `backend/dashboard/admin_dashboard.py`, `backend/dashboard/web_app_complete.py`
- Contains: Flask blueprints, HTML/CSS/JS templates, real-time WebSocket handlers
- Depends on: Google Sheets access, authentication, analytics, notifications
- Used by: Browsers (admin/finance staff)

**Cashier Application:**
- Purpose: Point-of-sale interface for processing transactions via RFID
- Location: `backend/dashboard/cashier/cashier_routes.py`
- Contains: Blueprint with cashier-specific routes, Arduino card reader integration, JWT auth
- Depends on: Arduino bridge, Google Sheets, transaction logging
- Used by: Cashier stations with Arduino + RFID hardware

**Business Logic Layer (Services):**
- Purpose: Core domain logic and operations
- Location: `backend/` (multiple modules: nfc_payments.py, fraud_detection.py, sync.py)
- Contains: Transaction processing, card management, fraud detection, synchronization
- Depends on: Error handling, logging
- Used by: All higher layers

**Infrastructure Layer (Support Services):**
- Purpose: Cross-cutting concerns and utilities
- Modules:
  - `cache.py`: TTL-based caching with LRU eviction
  - `resilience.py`: Retry logic with exponential backoff, rate limiting, write queue
  - `health.py`: System health monitoring and status reporting
  - `errors.py`: Centralized error handling and logging
  - `config_validator.py`: Configuration validation at startup
  - `connection_pool.py`: Connection pooling for Google Sheets
  - `notifications.py`: Email notifications via SMTP
  - `analytics.py`: Spending patterns and reporting
  - `exports.py`: CSV and Excel data export
  - `sync.py`: Multi-station synchronization with lock management

**Persistence Layer (Google Sheets):**
- Purpose: Long-term storage and state management
- Location: Google Sheets API accessed via gspread library
- Schema: Users, Money Accounts, Transactions Log, Lost Card Reports sheets
- Used by: All business logic and API layers

## Data Flow

**Transaction Processing Flow:**

1. Card scan at RFID reader (Arduino) → serial data
2. Arduino bridge receives and parses card UID
3. Cashier app validates card (student, money card pair)
4. Transaction creation with unique ID (sync.TransactionIDGenerator)
5. Write to Google Sheets Transactions Log (with retry via resilience.with_retry)
6. Balance update in Money Accounts sheet
7. Fraud detection analysis (fraud_detection.FraudDetector)
8. Notification dispatch if needed (notifications.EmailNotifier)
9. Real-time UI update via WebSocket (Flask-SocketIO)
10. Audit log maintained for reconciliation

**Data Read Flow:**

1. API/Dashboard request for data
2. Check TTL cache (cache.TTLCache) - 30 second default TTL
3. If cache miss: Query Google Sheets (gspread API)
4. Cache result with exponential backoff on API errors
5. Return to client with fallback to stale cache if sheets unavailable
6. Update metrics in health monitor (health.HealthMonitor)

**Sync & Locking Flow (Multi-Station):**

1. Station A acquires lock on transaction via sync.TransactionLock
2. Station B attempts same transaction - receives "busy" status
3. Lock timeout after 30 seconds or explicit release
4. Conflict detection by comparing transaction IDs
5. Duplicate transaction prevention via unique ID format: YYYYMMDD-HHMMSS-XXXX-RRRR

**State Management:**

- **Transaction State**: Captured in Google Sheets Transactions Log with status field
- **Card State**: Stored in Users and Money Accounts sheets
- **Session State**: In-memory dict (active_sessions in api_server.py) for JWT tokens
- **Virtual Cards**: Managed via nfc_payments.VirtualCard class (in-memory for current session)
- **Fraud Alerts**: Stored in-memory (fraud_detection.FraudDetector) with periodic export

## Key Abstractions

**Transaction ID Generator:**
- Purpose: Generate globally unique transaction IDs to prevent duplicates
- Examples: `backend/sync.py` (TransactionIDGenerator class)
- Pattern: YYYYMMDD-HHMMSS-STATION-HASH format with thread-safe counter

**Retry Configuration:**
- Purpose: Declarative retry logic with exponential backoff
- Examples: `backend/resilience.py` (RetryConfig, with_retry decorator)
- Pattern: Decorator-based with configurable attempts, delays, jitter

**Error Codes:**
- Purpose: Standardized error classification across all layers
- Examples: `backend/errors.py` (ErrorCode enum with 100+ specific codes)
- Pattern: Enum with ranges (1000-1099 config, 1100-1199 sheets, etc.)

**Health Status:**
- Purpose: Real-time monitoring of system components
- Examples: `backend/health.py` (HealthMonitor class)
- Pattern: Component-based status reporting with metrics aggregation

**Cache Entry:**
- Purpose: Metadata-rich cache entries with TTL and hit tracking
- Examples: `backend/cache.py` (CacheEntry, TTLCache classes)
- Pattern: LRU eviction with thread-safe access and statistics

**Fraud Alert:**
- Purpose: Structured representation of suspicious activity
- Examples: `backend/fraud_detection.py` (FraudAlert, FraudDetector classes)
- Pattern: Risk level and type classification with auto-resolution tracking

**Virtual Card:**
- Purpose: NFC phone payment via HCE (Host Card Emulation)
- Examples: `backend/nfc_payments.py` (VirtualCard class)
- Pattern: Linked to physical money card with PIN/biometric support

## Entry Points

**API Server:**
- Location: `backend/api/api_server.py` (main entry point: `app.run()`)
- Triggers: Manual startup with `python backend/api/api_server.py`
- Responsibilities: Mobile API for Android app, JWT auth, student/card lookup, balance queries, transaction endpoints

**Admin Dashboard:**
- Location: `backend/dashboard/admin_dashboard.py` (main entry point: `app.run()`)
- Triggers: Manual startup with `python backend/dashboard/admin_dashboard.py`
- Responsibilities: Admin UI, role-based access, analytics, reports, notifications, Arduino management

**Web-Only Dashboard:**
- Location: `backend/dashboard/web_app_complete.py` (alternative to admin_dashboard without Arduino deps)
- Triggers: Deployment scenario without hardware
- Responsibilities: Same as admin dashboard but no serial port/Arduino functionality

**Cashier Application:**
- Location: `backend/dashboard/cashier/cashier_routes.py` (registered as Blueprint)
- Triggers: Mounted at `/cashier` prefix on dashboard server
- Responsibilities: Point-of-sale interface, card reader integration, transaction processing

**Configuration Validation:**
- Location: `backend/config_validator.py`
- Triggers: Called on startup or manually with `python backend/config_validator.py`
- Responsibilities: Validate env vars, credentials, Google Sheets schema, serial ports

## Error Handling

**Strategy:** Layered error handling with specific error codes, recoverable flag, and centralized logging.

**Patterns:**

1. **Custom Exception Class (BankoError):**
   - All application errors inherit from `backend/errors.py::BankoError`
   - Contains: error_code (ErrorCode enum), message, details dict, recoverable flag
   - Usage: `raise BankoError(ErrorCode.STUDENT_NOT_FOUND, f"Student {id} not found")`

2. **Retry Decorator:**
   - Applied to Google Sheets API calls via `backend/resilience.py::@with_retry`
   - Exponential backoff with jitter (1s → 2s → 4s → ... max 30s)
   - Don't retry on non-recoverable errors (invalid request, auth failure)

3. **Graceful Degradation:**
   - Stale cache fallback when Sheets unavailable (`cache.py::allow_stale=True`)
   - Health status tracks component degradation (healthy/degraded/unhealthy)
   - Non-critical service failures don't block main transaction flow

4. **Validation:**
   - Input validation at API boundaries (type checking, required fields)
   - Schema validation for Google Sheets data (`config_validator.py`)
   - Card UID format validation in sync.TransactionIDGenerator

5. **Logging:**
   - Structured logging via `backend/errors.py::get_logger()`
   - Different log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Request tracking and audit trail in Transactions Log

## Cross-Cutting Concerns

**Logging:**
- Framework: Python logging module via `backend/errors.py::setup_logging()`
- Files: Logs written to `logs/` directory with rotation
- Pattern: Centralized logger obtained via `get_logger()` in all modules

**Validation:**
- Input validation: Decorators and helper functions in relevant modules
- Schema validation: ConfigValidator checks Google Sheets structure on startup
- Card ID validation: sync.TransactionIDGenerator validates transaction ID format

**Authentication:**
- Mechanism: JWT tokens (HS256 algorithm)
- Storage: HTTP-only cookies (cashier), Bearer tokens (API clients)
- Roles: student, admin, finance, cashier with role-based access control
- Token expiry: 24 hours for API, 8 hours for cashier sessions

**Rate Limiting:**
- Framework: `backend/resilience.py::get_rate_limiter()`
- Pattern: Token bucket per user/endpoint to prevent abuse
- Defaults: Configurable limits to prevent Google Sheets API quota exhaustion

**Caching:**
- Strategy: TTL-based cache with 30-second default for Google Sheets data
- LRU eviction: When max_size (100 entries) exceeded, remove least-recently-used
- Stale fallback: Allow serving stale data if Sheets is unavailable
- Invalidation: Pattern-based cache invalidation on write operations

**Timezone:**
- Standard: Asia/Manila (PHILIPPINES_TZ) used throughout
- Implementation: All datetime operations use `pytz` for consistency
- Pattern: Helper function `get_philippines_time()` in each module

---

*Architecture analysis: 2026-02-22*
