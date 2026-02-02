# Banko ng Seton: 2026 Strategic Roadmap

## 🌟 Vision
To modernize the **Banko ng Seton** school finance system into a reliable, performant platform while retaining its accessible **Google Sheets** database. The goal is to maximize stability, user experience, and maintainability without complex infrastructure migration.

## 🗺️ Phases & Milestones

### Phase 0: Foundation (Stability First)
**Goal:** Establish testing and error handling before optimization.
**Success Metrics:** 100% core function test coverage, standardized error responses

- [ ] **Test Suite Implementation**
    - Add pytest framework with fixtures for Google Sheets mocking
    - Write tests for card verification, balance updates, transaction logging
    - Test serial communication protocol edge cases
- [ ] **Error Handling Standardization**
    - Centralize exception handling with consistent logging
    - Create structured error responses (JSON format)
    - Add error recovery for Google Sheets API failures
- [ ] **Configuration Validation**
    - Validate all required `.env` variables on startup
    - Check Google Sheets connectivity and schema on boot
    - Verify Arduino serial port availability before operations
- [ ] **Documentation Improvements**
    - Document serial protocol edge cases and timeouts
    - Add troubleshooting guide for common errors
    - Create developer setup checklist

### Phase 1: Reliability & Performance
**Goal:** Make the system fast and resilient to network issues.
**Success Metrics:** Dashboard loads <500ms, 99% uptime, zero data loss on network failures

- [ ] **In-Memory Caching Layer**
    - Implement TTL-based cache (30-60s) for frequently accessed data
    - Cache student records, balances, recent transactions
    - **Outcome:** Instant dashboard loads, reduced API calls by 80%
- [ ] **Google Sheets API Resilience**
    - Add exponential backoff retry logic (max 3 attempts)
    - Implement request batching for bulk operations
    - Queue failed writes for retry on reconnection
- [ ] **Health Monitoring**
    - Add `/health` endpoint showing system status
    - Monitor Google Sheets API quota usage
    - Track Arduino serial connection health
- [ ] **Sync Status Indicators**
    - Add visual indicators: online/offline/syncing/error
    - Show "last synced" timestamp on dashboard
    - Queue transactions locally when offline, sync when back online

### Phase 2: User Experience (PWA)
**Goal:** Accessible anywhere, on any device, with better UX.
**Success Metrics:** <3s first load, works offline, mobile-friendly

- [ ] **PWA Conversion**
    - Add `manifest.json` with app icons (192x192, 512x512)
    - Implement Service Worker for static asset caching
    - Enable "Add to Home Screen" on mobile devices
    - **Outcome:** Dashboard installable as native-like app
- [ ] **Progressive UI Updates**
    - Show "pending" badges for transactions being synced
    - Display optimistic updates with rollback on failure
    - Add loading skeletons instead of blank screens
- [ ] **Mobile App Enhancements**
    - Implement biometric authentication (fingerprint/face unlock)
    - Add pull-to-refresh for balance updates
    - Improve transaction history UI with search/filter
- [ ] **Accessibility Improvements**
    - Add proper ARIA labels for screen readers
    - Ensure keyboard navigation works throughout
    - Test with high contrast mode

### Phase 3: Smart Features & Analytics
**Goal:** Provide actionable insights without over-engineering.
**Success Metrics:** Students check app weekly, admins use reports monthly

- [ ] **Simple Analytics Dashboard**
    - Daily/weekly/monthly spending totals by student
    - Most popular purchase times (identify peak hours)
    - Low balance warnings (email/push when balance < threshold)
    - Top spenders report for admin review
- [ ] **Export Capabilities**
    - Export transaction reports to PDF/Excel
    - Generate monthly statements per student
    - Create audit logs for compliance
- [ ] **Transaction Dispute System**
    - Manual flagging for disputed transactions
    - Admin review workflow with notes
    - Status tracking: Pending/Resolved/Rejected
- [ ] **Notification System**
    - Email/push alerts for low balance (<₱50)
    - Parent notifications for large transactions (>₱100)
    - Daily transaction summary option

### Phase 4: Scale & Advanced Features ✅
**Goal:** Prepare for growth and future hardware capabilities.
**Success Metrics:** Support 500+ students, <2s transaction time

- [x] **NFC Phone Payments (HCE)**
    - Abstract NFC handling in Android app
    - Implement Host Card Emulation for phone-based payments
    - Add security layer (biometric + PIN for high-value)
- [x] **Multi-Station Synchronization**
    - Implement distributed locking for concurrent writes
    - Add transaction ID generation to prevent duplicates
    - Test with multiple cashier stations simultaneously
- [x] **Advanced Fraud Detection**
    - Pattern analysis: Unusual transaction amounts/times
    - Location-based verification (if stations are tracked)
    - Automatic card suspension on suspicious activity
- [x] **Performance Optimization**
    - Profile and optimize slow database queries
    - Add connection pooling for Google Sheets API
    - Consider Redis for distributed caching (if needed)

## 🛠️ Technical Strategy

### Architecture
- **Database:** Google Sheets (Primary Source of Truth)
- **Backend:** Flask + Python with in-memory caching
- **Caching:** Dict-based cache with TTL (Redis optional for multi-process)
- **Frontend:** HTML/CSS/JS enhanced with PWA capabilities
- **Mobile:** Android (Kotlin) with Retrofit API client

### Key Design Patterns
1. **Helper Functions:** Simple Google Sheets wrapper functions (avoid over-abstraction)
2. **Command Queue:** For offline transaction queuing and retry logic
3. **Observer Pattern:** WebSockets for real-time Arduino → Dashboard updates
4. **Service Layer:** Separate business logic from Flask routes

### Code Hygiene & Refactoring Strategy
- **Clean Slate Policy:** When upgrading a feature, delete the old implementation to prevent bloat
- **No Dead Code:** Commented-out legacy code is forbidden. Remove immediately or use git for history
- **Migration Path:** Ensure new implementation has feature parity before deleting old code
- **Safety Net:** Keep old code in git tags for 30 days post-deployment before removal (allows rollback)
- **Documentation:** Update relevant docs when removing/changing features

## 📊 Success Metrics Summary

| Phase | Key Metric | Target |
|-------|-----------|--------|
| Phase 0 | Test Coverage | 100% core functions |
| Phase 1 | Dashboard Load Time | <500ms |
| Phase 1 | System Uptime | 99% |
| Phase 2 | First Load Time | <3s |
| Phase 3 | User Engagement | Weekly app opens |
| Phase 4 | Transaction Speed | <2s end-to-end |

## 📝 Progress Tracking
See [PROGRESS.md](PROGRESS.md) for detailed implementation status and milestones.

