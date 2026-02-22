# Codebase Concerns

**Analysis Date:** 2026-02-22

## Tech Debt

**Excessive Debug Print Statements:**
- Issue: 60+ `print()` statements scattered throughout `backend/dashboard/admin_dashboard.py` (1,766 LOC), making production logs cluttered and harder to parse
- Files: `backend/dashboard/admin_dashboard.py` (lines throughout), `backend/api/api_server.py` (scattered)
- Impact: Production logs become unreadable; difficult to filter real errors from debug noise; violates structured logging best practices
- Fix approach: Replace all debug prints with proper logging using `get_logger()` (already available in `backend/errors.py`). Set log levels (DEBUG, INFO, ERROR) and configure via environment variables

**Weak Secret Management:**
- Issue: Default Flask secret key `'bangko-admin-secret-key-change-in-production'` is exposed in code and left as fallback. Printed to stdout at startup: line 1752 in `admin_dashboard.py` prints `f"✓ Finance login: {finance_user} / {finance_pass}"`
- Files: `backend/dashboard/admin_dashboard.py` (lines 61, 1752-1757), `backend/api/api_server.py` (line 23)
- Impact: Session tokens become predictable; credentials exposed in logs/console output; attackers can forge admin sessions
- Fix approach: Enforce non-empty FLASK_SECRET_KEY via config validation; remove credential printing from startup output; use environment-only credential storage

**Manual Global State Management:**
- Issue: Multiple global variables directly mutated without synchronization: `arduino`, `db`, `card_reading_active`, `pending_student_id` in `admin_dashboard.py` (lines 74-82)
- Files: `backend/dashboard/admin_dashboard.py` (lines 74-82)
- Impact: Race conditions possible in concurrent access; no transaction safety; card reading state can become inconsistent
- Fix approach: Wrap globals in a thread-safe singleton class; use proper locking around state changes

**Hardcoded Card Normalization Logic:**
- Issue: `normalize_card_uid()` (line 129 in `api_server.py`) strips leading zeros, but this logic is duplicated across multiple files without specification
- Files: `backend/api/api_server.py` (line 129), used in `admin_dashboard.py` (multiple calls)
- Impact: Card matching could fail silently if normalization is inconsistent; no clear contract about UID format
- Fix approach: Define UID format spec; centralize normalization in a single utility; add validation tests

---

## Known Bugs

**Potential Null Card UID Issue:**
- Symptoms: If a card reads as empty or malformed, `normalize_card_uid('')` returns empty string, which matches other empty cards as duplicates
- Files: `backend/dashboard/admin_dashboard.py` (lines 1083-1089, 1142)
- Trigger: Arduino sends malformed/empty card UID; checks compare normalized empty strings
- Workaround: Validate UID format before normalization; reject empty UIDs at source
- Fix approach: Add `if not uid: raise ValueError()` before any duplicate checks

**Missing Error Handling on Sheets Failures:**
- Symptoms: Transient Google Sheets API failures cause 500 errors; no graceful fallback or retry at API level
- Files: `backend/api/api_server.py` (lines 43-57, 69-73), `admin_dashboard.py` (lines 91-102)
- Trigger: Network timeout; quota exceeded; temporary Google API outage
- Current mitigation: `get_worksheet_with_retry()` retries 2x, but no backoff on specific error types
- Fix approach: Distinguish between retryable (429, 503) and permanent (401, 404) errors; implement exponential backoff; cache stale data as fallback

---

## Security Considerations

**CORS Disabled Validation:**
- Risk: `CORS(app, cors_allowed_origins="*")` in `admin_dashboard.py` (line 64) and `api_server.py` line 35 opens all cross-origin requests without validation
- Files: `backend/dashboard/admin_dashboard.py` (line 64), `backend/api/api_server.py` (line 35)
- Current mitigation: SocketIO CORS also set to "*"
- Recommendations: Restrict CORS to known origins (e.g., student app domain); validate origin header; remove wildcard for production

**No Input Validation on Card UID:**
- Risk: Card UIDs are used directly in Google Sheets queries without length/format validation; could allow injection if Sheets API changes
- Files: `backend/dashboard/admin_dashboard.py` (line 1045 reads raw card, used in lines 1073-1114 without validation)
- Current mitigation: Length check `if len(uid) == 8` (line 1046)
- Recommendations: Add regex validation for UID format; sanitize before use in Sheets API calls

**Default Hardcoded Credentials in Tests:**
- Risk: Test files `test_phase1.py` (line 21: `JWT_SECRET = "test-secret-key"`) and `test_phase3.py` (lines 18, 93: hardcoded passwords) could be leaked if copied to production
- Files: `backend/test_phase1.py` (line 21), `backend/test_phase3.py` (lines 18, 69, 93, 124)
- Impact: Trivial to forge JWTs; cashier system easily compromised
- Recommendations: Use environment variables for all secrets, even in tests; add `.env.test` to `.gitignore`

**Admin Login Accepts Empty Credentials:**
- Risk: Line 221 in `admin_dashboard.py` allows login if `admin_user == ""` and `admin_pass == ""`, meaning blank username/password is valid
- Files: `backend/dashboard/admin_dashboard.py` (line 221)
- Current mitigation: None; this is intentional fallback
- Recommendations: Require explicit admin credentials; if fallback needed, log security warning; use one-time setup password

---

## Performance Bottlenecks

**Unbounded Worksheet Scans:**
- Problem: Every card registration, transaction, or product access calls `get_all_records()` which reads entire sheet into memory. On large sheets (1000+ users), this is O(n) per request
- Files: `backend/dashboard/admin_dashboard.py` (lines 1078, 1137, 1152, 1261); `api_server.py` (line 156, 178)
- Cause: No indexing on StudentID, CardNumber, etc.; linear search through all records
- Improvement path: (1) Add unique indexes to Google Sheets data via custom format; (2) Cache frequently accessed ranges; (3) Batch queries; (4) Consider moving to a real database

**Excessive Cache Misses on Global Sheet Data:**
- Problem: `_sheets_cache` in `admin_dashboard.py` (line 82) has 30-second TTL but is not cleared when data changes; high write frequency invalidates cache constantly
- Files: `backend/dashboard/admin_dashboard.py` (line 82-83)
- Cause: Manual cache with no invalidation strategy; timestamps not coordinated with sheet updates
- Improvement path: Use `backend/cache.py` TTLCache instead; implement invalidation patterns on write

**Synchronous Email Sending Blocking Transactions:**
- Problem: Even with async retry in `email_service.py`, SMTP failures timeout synchronously (default socket timeout ~30s per attempt × 3 retries = 90s wait)
- Files: `backend/services/email_service.py` (lines 82-84)
- Cause: No request timeout configured; SMTP library defaults to blocking I/O
- Improvement path: Set explicit socket timeout (e.g., 5s); use non-blocking SMTP or deferred queue; parallelize email sends

---

## Fragile Areas

**Arduino Serial Communication State Machine:**
- Files: `backend/dashboard/admin_dashboard.py` (lines 1022-1067 thread loop), `arduino_bridge.py`
- Why fragile: Global `card_reading_active` flag shared between main thread and reader thread with only 30-second timeout; no timeout on main thread waiting for response
- Safe modification: (1) Use threading.Event instead of flag; (2) Add response queue; (3) Implement proper thread lifecycle (start, wait, stop); (4) Add timeout handling at all levels
- Test coverage: No unit tests for thread safety; race condition between `socketio.emit()` in reader thread and Flask route handler

**Card Normalization Inconsistency:**
- Files: `backend/api/api_server.py` (line 129), `admin_dashboard.py` (duplicated logic)
- Why fragile: Two places strip leading zeros but no shared test suite ensures they match; if one changes, duplicates silently break
- Safe modification: Extract to `backend/utils.py` card_utils module; add tests; import everywhere
- Test coverage: No tests for UID normalization; edge cases like all-zeros UID, non-hex characters untested

**Money Card Balance Deduction Without Transaction Atomicity:**
- Files: `backend/api/api_server.py` (transaction flow); `admin_dashboard.py` (card linking)
- Why fragile: If balance deduction fails mid-update, card is linked but balance not decremented; no rollback
- Safe modification: Use Google Sheets batch updates with error handling; add transaction log before balance change; implement idempotency keys
- Test coverage: No integration tests for failure scenarios (e.g., Sheets API failure mid-transaction)

---

## Scaling Limits

**Single-Instance Google Sheets Bottleneck:**
- Current capacity: ~1,000 requests/minute per Google Sheets project quota (burst limit 500)
- Limit: Each transaction + email + logging hits Sheets multiple times; 100 cashier stations × 10 TPS = 1,000 TPS would exceed quota in seconds
- Scaling path: (1) Implement dual-database (Sheets for config, PostgreSQL for transactions); (2) Batch writes; (3) Request quota increase with Google; (4) Use BigQuery export instead of direct Sheets queries

**Fixed Thread Pool in read_card_thread:**
- Current capacity: Each card read spawns a new thread (`thread = threading.Thread(...)`); no pooling
- Limit: 100+ concurrent card reads = 100+ threads consuming memory
- Scaling path: Use ThreadPoolExecutor(max_workers=10) for card reader threads; queue reads

**In-Memory Cache Max Size:**
- Current capacity: `TTLCache(max_size=200)` in `cache.py` (line 206); with LRU eviction
- Limit: 200 entries not enough for multi-school deployments
- Scaling path: (1) Increase max_size; (2) Add disk-based cache fallback (SQLite); (3) Use Redis for distributed caching

---

## Dependencies at Risk

**oauth2client Deprecated:**
- Risk: `oauth2client` (imported in `admin_dashboard.py`, `api_server.py`) is deprecated since 2017; no longer maintained
- Impact: Security patches not applied; incompatible with Python 3.12+; missing OAuth 2.0 improvements
- Migration plan: Replace with `google-auth` library; requires credential format change (JSON service account → google-auth compatible)

**Outdated JWT Handling:**
- Risk: Using `jwt.encode()` without explicit `algorithms` parameter (deprecated); could silently fail on library updates
- Files: `backend/api/api_server.py` (line 90)
- Current mitigation: `algorithm='HS256'` is specified
- Recommendation: Pin PyJWT version; add deprecation tests

---

## Missing Critical Features

**No Transaction Idempotency Protection:**
- Problem: If client retries a purchase (due to timeout), backend processes it twice
- Blocks: Cannot safely retry failed transactions; duplicate charges possible
- Recommendation: Add idempotency key (UUID) to transaction requests; store processed keys for 24 hours

**No Audit Logging:**
- Problem: Admin actions (change password, register card, process transaction) not logged with user/timestamp
- Blocks: Compliance; fraud investigation; accountability
- Recommendation: Add audit log table in Sheets or DB; log all admin actions with user context

**No Card Expiration/Validity Tracking:**
- Problem: Stolen or lost cards cannot be permanently disabled; only "Status" flag on Users sheet
- Blocks: Cannot prevent old card from being re-registered
- Recommendation: Add card validity dates; timestamp card creation; archive old cards

---

## Test Coverage Gaps

**No Integration Tests for Multi-Station Sync:**
- What's not tested: Concurrent transactions from multiple cashier stations; lock acquisition; deadlock scenarios
- Files: `backend/sync.py` (distributed lock logic); `admin_dashboard.py` (transaction processing)
- Risk: Race conditions causing duplicate transactions or balance inconsistencies
- Priority: HIGH - This is production-critical

**No Error Injection Tests:**
- What's not tested: Behavior when Google Sheets API fails; network timeouts; malformed responses
- Files: `backend/api/api_server.py`, `admin_dashboard.py` (all sheet operations)
- Risk: Silent failures or confusing error messages in production
- Priority: HIGH - Happens frequently with flaky networks

**No UI Test Coverage for Cashier Flow:**
- What's not tested: End-to-end cashier payment flow; Arduino integration; WebSocket communication
- Files: `backend/dashboard/cashier/` (entire payment flow), `admin_dashboard.py` (card reading)
- Risk: Payment failures go undetected; UI state desynchronization
- Priority: MEDIUM - Can be manual testing, but should be automated

**No Security Tests:**
- What's not tested: CORS bypass attempts; SQL injection via card UID; JWT token forgery; brute force login
- Files: All API routes
- Risk: Security vulnerabilities undetected
- Priority: HIGH - Must test before production

---

*Concerns audit: 2026-02-22*
