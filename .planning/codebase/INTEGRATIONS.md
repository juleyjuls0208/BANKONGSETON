# External Integrations

**Analysis Date:** 2026-02-22

## APIs & External Services

**Google Sheets API:**
- Service: Google Sheets (primary data persistence)
- What it's used for: Student records, transaction history, balance management, card information
- SDK/Client: `gspread` 5.12.0
- Auth: OAuth 2.0 via `oauth2client` 4.1.3 using Service Account credentials
- Config: `/config/credentials.json` (Service Account JSON file)
- Environment: `GOOGLE_SHEETS_ID` - spreadsheet ID
- Implementation files:
  - `backend/api/api_server.py` - Mobile API access to sheets
  - `backend/dashboard/admin_dashboard.py` - Admin dashboard sheets access
  - `backend/resilience.py` - Retry logic and error handling for sheets operations

**Arduino Serial Communication:**
- Service: Arduino RFID readers (hardware integration)
- What it's used for: Card reading and RFID detection
- SDK: `pyserial` 3.5
- Connection: USB serial ports
- Config: `SERIAL_PORT`, `ADMIN_PORT`, `BAUD_RATE` (default 9600)
- Implementation files:
  - `backend/dashboard/arduino_bridge.py` - Serial communication bridge
  - `backend/dashboard/cashier/cashier_routes.py` - Cashier RFID card reading

## Data Storage

**Databases:**
- Type/Provider: Google Sheets (cloud-based, no traditional database)
- Sheets: Students, Transactions, Cards, Analytics, Monthly Statements
- ORM/Client: gspread (spreadsheet-as-database approach)
- Connection: OAuth 2.0 authenticated API calls
- Environment: `GOOGLE_SHEETS_ID`

**File Storage:**
- Local filesystem only for temporary data
- Excel/CSV export generation in: `backend/exports.py`
- Log files in: `logs/` directory
- Coverage reports in: `coverage_report/` directory

**Caching:**
- In-memory caching layer: `backend/cache.py`
- Purpose: Reduce Google Sheets API calls
- Timeout: 30 seconds (configurable in code)
- Session storage: In-process dictionary (production uses in-memory)

## Authentication & Identity

**Auth Provider:**
- Custom implementation (no external auth provider)
- Approach:
  - Admin/Finance dashboard: Session-based authentication (Flask sessions)
  - Mobile API: JWT token-based authentication
  - JWT Implementation: `pyjwt` 2.8.0
  - Algorithm: HS256
  - Token expiry: 24 hours (configurable)
  - Session secret: `FLASK_SECRET_KEY` environment variable

**API Security:**
- JWT token validation in: `backend/api/api_server.py` (functions `generate_jwt_token`, `verify_jwt_token`)
- Credentials: `backend/dashboard/cashier/cashier_routes.py` (JWT verification)
- Encryption: `cryptography` 41.0.7 for secure token handling

## Monitoring & Observability

**Error Tracking:**
- Custom error handling system: `backend/errors.py`
- Error codes mapped for: Google Sheets errors, serial port errors, transaction errors
- Implementation: `ErrorCode` enum with specific error categories
- Logging: File and console logging via standard Python logging

**Logs:**
- Approach: Python logging module with file rotation
- Log directory: `logs/` (created at runtime)
- Health status tracking: `backend/health.py`
- Uptime statistics: Available via health check endpoints
- Request recording: Automatic request logging to health tracking

**Analytics:**
- Module: `backend/analytics.py`
- Tracks: Spending patterns, transaction distribution, student activity
- Data source: Google Sheets transaction history
- Export format: JSON summaries

## CI/CD & Deployment

**Hosting:**
- Backend: Manually deployed Python server (Flask + gunicorn)
- Admin Dashboard: Served by Flask development or gunicorn server
- Mobile: Google Play Store distribution (Android)
- No Docker containerization configured

**CI Pipeline:**
- None detected - manual testing and deployment
- Test framework configured: pytest with coverage reporting
- Test command: `pytest` with coverage to HTML report

**Deployment Artifacts:**
- `backend/dashboard/wsgi.py` - WSGI entry point for production servers

## Environment Configuration

**Required Environment Variables (Critical):**
- `GOOGLE_SHEETS_ID` - Spreadsheet identifier
- `SERIAL_PORT` - Arduino COM port or /dev/ttyXXX
- `BAUD_RATE` - Serial communication speed (default: 9600)
- `FLASK_SECRET_KEY` - Session encryption key
- `API_PORT` - API server port (default: 5001)

**Optional Environment Variables:**
- `DEBUG_MODE` - Enable debug logging
- `OFFLINE_MODE` - Fallback for Google Sheets unavailability
- `AUTO_ATTENDANCE` - Automatic attendance marking
- `ADMIN_USERNAME` - Admin login username
- `ADMIN_PASSWORD` - Admin login password
- `FINANCE_USERNAME` - Finance user login
- `FINANCE_PASSWORD` - Finance user password
- `TRANSACTION_TIMEOUT` - Transaction timeout (default: 60s)
- `LOW_BALANCE_THRESHOLD` - Balance warning level (default: 50.00)
- `MAX_TRANSACTION_AMOUNT` - Transaction limit (default: 500.00)
- `MIN_BALANCE_ALLOWED` - Minimum balance (default: 0.00)

**Email Configuration (Optional):**
- `SMTP_SERVER` - Email server address (e.g., smtp.gmail.com)
- `SMTP_PORT` - Email server port (default: 587)
- `SMTP_USER` - Email account username
- `SMTP_PASSWORD` - Email account password
- `FROM_EMAIL` - Sender email address
- Implementation: `backend/notifications.py` (EmailNotifier class)

**Secrets Location:**
- `.env` file (not committed to git, template at `.env.example`)
- `/config/credentials.json` - Google Service Account (not committed)
- Credentials path resolution: `config/credentials.json` or fallback to current directory

## Webhooks & Callbacks

**Incoming:**
- None detected - system uses polling for Google Sheets data

**Outgoing:**
- Email notifications to parent addresses
- Firebase Cloud Messaging push notifications (optional, in student_app_v2)
- Implementation: `backend/notifications.py` with SMTP-based email delivery

**Real-time Communication:**
- WebSocket support via Flask-SocketIO 5.3.0
- Used for: Live dashboard updates, real-time transaction notifications
- Implementation: `backend/dashboard/admin_dashboard.py` with `socketio` instance

## Mobile App Integration

**Android HTTP Communication:**
- Client: Retrofit 2.9.0 with OkHttp 4.11.0
- Base endpoint: Backend Flask API at `API_PORT` (5001)
- JSON serialization: Gson 2.10.1
- Logging interceptor: OkHttp logging for debugging

**Firebase Integration (student_app_v2 only):**
- Service: Firebase Cloud Messaging
- Version: BOM 32.7.0
- Purpose: Push notifications for transaction alerts
- Implementation: `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/FCMService.kt`
- Configuration: Requires `google-services.json` (not in repo)

**Secure Storage (Android):**
- Encrypted preferences: `androidx.security:security-crypto`
- Purpose: Store JWT tokens and user credentials securely
- Implementation: DataStore and encrypted SharedPreferences

---

*Integration audit: 2026-02-22*
