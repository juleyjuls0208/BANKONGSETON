# BankongSeton Documentation

BankongSeton is a school canteen cashless payment system. Students pay for food by tapping their
RFID card at the cashier terminal. This directory contains the complete technical documentation for
developers who want to understand, set up, extend, or operate the system.

---

## Documents

| Document | What it covers | Good starting point if you want to... |
|----------|----------------|---------------------------------------|
| [Architecture Overview](architecture.md) | System layers, dual-server setup, auth split, data flow | Understand how the system fits together |
| [Setup Guide](setup.md) | Install, configure, and run the system from scratch | Get the system running on a new machine |
| [API Reference](api-reference.md) | All 12 REST endpoints: auth, request/response shapes, JSON examples | Build a client or debug API calls |
| [Google Sheets Schema](google-sheets-schema.md) | All 7 sheets, exact column layout, relationships | Query or extend the database |
| [Cashier Guide](cashier-guide.md) | Cashier POS web app, Arduino wiring, card-tap-to-transaction flow | Operate or troubleshoot the cashier terminal |
| [Admin Guide](admin-guide.md) | Admin dashboard features, roles, product and student management | Manage the system day-to-day |
| [Student App](student-app.md) | Android app architecture, screens, API calls, FCM setup | Develop or modify the Android student app |
| [NFC Integration Guide](nfc-integration-guide.md) | HCE implementation guide for Android v2 NFC payments | Implement NFC tap-to-pay on Android |

---

## Quick Links

- **New developer?** Start with [Architecture Overview](architecture.md), then [Setup Guide](setup.md)
- **Setting up a new server?** See [Setup Guide](setup.md)
- **Calling the API?** See [API Reference](api-reference.md)
- **Arduino not reading cards?** See [Cashier Guide](cashier-guide.md) troubleshooting
- **Implementing NFC v2?** See [NFC Integration Guide](nfc-integration-guide.md)

---

## System Summary

| Component | Technology |
|-----------|------------|
| Backend API | Python 3 / Flask (port 5001) |
| Admin Dashboard + Cashier POS | Python 3 / Flask (port 5003) |
| Database | Google Sheets (gspread + google-auth) |
| Android App | Kotlin (Retrofit + EncryptedSharedPreferences) |
| Hardware | Arduino + RC522 RFID reader |
| Push Notifications | Firebase Cloud Messaging |

---

## Documentation Archive

The `archive/` subdirectory contains earlier documentation from the project's development phases.
These may be useful for historical context but may not reflect the current system accurately.
