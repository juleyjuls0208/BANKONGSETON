# Technology Stack

**Analysis Date:** 2026-02-22

## Languages

**Primary:**
- Python 3.12+ - Backend APIs and dashboards
- Kotlin/Java - Android mobile applications
- HTML/CSS/JavaScript - Web dashboard templates and frontend

**Secondary:**
- C/Arduino - RFID card reader firmware (firmware stored externally)

## Runtime

**Environment:**
- Python 3.12 (development environment: 3.14.3)
- Java 11 (Android compilation)
- Kotlin (Android primary language)

**Package Manager:**
- pip (Python dependencies)
- Gradle (Android dependencies)
- Maven Central Repository (Android artifacts)

**Lockfile:**
- `requirements.txt` for Python dependencies
- `requirements-test.txt` for test dependencies
- Gradle lock files for Android (implicit through build.gradle.kts)

## Frameworks

**Core Backend:**
- Flask 3.0.0 - Web framework and admin dashboard
- Flask-CORS 4.0.0 - Cross-origin resource sharing
- Flask-SocketIO 5.3.0 - WebSocket support for real-time updates
- gunicorn 21.2.0 - Production WSGI server

**Android:**
- AndroidX (core-ktx 1.12.0, appcompat 1.6.1, activity 1.8.2)
- Jetpack Compose (BOM 2024.01.00) - Declarative UI framework for student app
- Material Design 3 (androidx.compose.material3)
- AndroidX Lifecycle (2.7.0) - ViewModel and Lifecycle management
- AndroidX Navigation (2.7.6) - App navigation for Compose

**Testing:**
- pytest 7.4.0 - Python test framework
- pytest-cov 4.1.0 - Coverage reporting
- pytest-flask 1.2.0 - Flask testing utilities
- pytest-mock 3.11.1 - Mocking support
- responses 0.23.1 - HTTP mocking
- freezegun 1.2.2 - Time manipulation for tests
- faker 19.2.0 - Fake data generation
- JUnit 4.13.2 - Android unit testing
- Espresso 3.5.1 - Android UI testing

**Build/Dev:**
- Gradle (Android build system)
- Kotlin Compiler (1.5.5 for Compose)

## Key Dependencies

**Critical:**
- gspread 5.12.0 - Google Sheets API client (core data persistence)
- oauth2client 4.1.3 - OAuth 2.0 authentication for Google Sheets
- pyserial 3.5 - Serial communication with Arduino/RFID readers
- pyjwt 2.8.0 - JWT token generation and validation for API authentication
- python-dotenv 1.0.0 - Environment variable management

**Infrastructure:**
- cryptography 41.0.7 - Encryption for sensitive data
- psutil 5.9.0 - System and process monitoring
- pytz 2024.1 - Timezone management (Philippines timezone)
- openpyxl 3.1.0 - Excel file generation for exports

**Android Networking:**
- Retrofit 2.9.0 - Type-safe HTTP client
- OkHttp 4.11.0 - HTTP client with logging interceptor
- Gson 2.10.1 - JSON serialization/deserialization

**Android Storage & Security:**
- androidx.security:security-crypto 1.1.0-alpha06 - Encrypted SharedPreferences
- androidx.datastore:datastore-preferences 1.0.0 - Key-value data persistence
- androidx.preference:preference-ktx 1.2.1 - Shared preferences wrapper

**Android Async:**
- kotlinx-coroutines-core 1.7.3 - Async/await for Kotlin
- kotlinx-coroutines-android 1.7.3 - Android coroutine integration
- accompanist-swiperefresh 0.32.0 - Swipe-to-refresh for Compose UI

**Cloud & Messaging:**
- firebase-messaging-ktx (BOM 32.7.0) - Firebase Cloud Messaging for push notifications (student_app_v2)
- com.google.gms:google-services - Google Services plugin for Android

## Configuration

**Environment Variables Required:**
- `GOOGLE_SHEETS_ID` - Google Sheets spreadsheet identifier
- `SERIAL_PORT` - Arduino serial connection port (COM3, /dev/ttyUSB0, etc.)
- `ADMIN_PORT` - Admin interface serial port
- `BAUD_RATE` - Serial communication baud rate (default: 9600)
- `FLASK_SECRET_KEY` - Flask session encryption key
- `API_PORT` - Backend API server port (default: 5001)
- `JWT_SECRET` - JWT token signing secret
- `DEBUG_MODE` - Enable debug logging
- `OFFLINE_MODE` - Offline operation fallback
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` - Email notification configuration

**Configuration Files:**
- `.env` - Environment variables (not committed, template at `.env.example`)
- `/config/credentials.json` - Google Service Account credentials (not committed)

**Transaction Settings (environment variables):**
- `TRANSACTION_TIMEOUT` - Transaction timeout in seconds (default: 60)
- `LOW_BALANCE_THRESHOLD` - Warning threshold for student balance
- `MAX_TRANSACTION_AMOUNT` - Maximum single transaction limit
- `MIN_BALANCE_ALLOWED` - Minimum allowed balance

## Platform Requirements

**Development:**
- Python 3.12+
- Android SDK 34+ (compileSdk: 34)
- Java 11+
- Arduino IDE or compatible serial tools
- Git

**Production:**
- Linux/Windows server capable of running Python 3.12
- SMTP server access for email notifications
- Google Service Account with Sheets API enabled
- USB serial port for Arduino RFID readers
- Optional: Firebase project for push notifications

**Android Target:**
- Minimum SDK: 24 (Android 7.0)
- Target SDK: 34 (Android 14)
- Architectures: arm64-v8a (Compose app), arm64-v8a + armeabi-v7a (material app)

---

*Stack analysis: 2026-02-22*
