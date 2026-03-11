# Bangko ng Seton - Student App V2

Modern Android student banking app with clean architecture.

## Features

- ✅ Student login with Student ID
- ✅ Real-time balance display with pull-to-refresh
- ✅ Transaction history with itemized receipts
- ✅ Dark mode toggle
- ✅ Secure encrypted storage
- ✅ Push notifications (FCM)
- ✅ Material Design 3

## Tech Stack

- **Kotlin** - Primary language
- **Android Views** - Traditional UI (not Compose)
- **Retrofit** - API client
- **EncryptedSharedPreferences** - Secure storage
- **Material Components** - UI components
- **Firebase Cloud Messaging** - Push notifications
- **RecyclerView** - Transaction list
- **SwipeRefreshLayout** - Pull to refresh

## Project Structure

```
app/src/main/
├── java/com/bankongseton/student/
│   ├── MainActivity.kt         # Entry point
│   ├── LoginActivity.kt        # Login screen
│   ├── HomeActivity.kt         # Balance display
│   ├── TransactionsActivity.kt # Transaction history
│   ├── SettingsActivity.kt     # Settings & logout
│   ├── TransactionsAdapter.kt  # RecyclerView adapter
│   ├── ApiClient.kt           # Retrofit API client
│   ├── Models.kt              # Data models
│   ├── SecureStorage.kt       # Encrypted storage
│   └── FCMService.kt          # Firebase messaging
└── res/
    └── layout/
        ├── activity_login.xml
        ├── activity_home.xml
        ├── activity_transactions.xml
        ├── activity_settings.xml
        └── item_transaction.xml
```

## Build Instructions

### Prerequisites

- Android Studio Hedgehog (2023.1.1) or later
- JDK 11
- Android SDK 34
- Firebase account (for FCM)

### Setup

1. **Open Project in Android Studio**
   ```
   File -> Open -> Select mobile/student_app_v2
   ```

2. **Configure API Endpoint**
   
   Edit `ApiClient.kt`:
   ```kotlin
   private const val BASE_URL = "http://YOUR_SERVER_IP:5001/api/"
   ```

3. **Add Firebase Configuration**
   
   Download `google-services.json` from Firebase Console and place in `app/` directory.

4. **Sync Gradle**
   ```
   File -> Sync Project with Gradle Files
   ```

5. **Build APK**
   ```
   Build -> Build Bundle(s) / APK(s) -> Build APK(s)
   ```

## API Configuration

Update the base URL in `ApiClient.kt`:
```kotlin
private const val BASE_URL = "http://192.168.68.122:5001/api/"
```

## Testing

1. Connect Android device or start emulator
2. Click Run (Shift+F10)
3. Test login with Student ID
4. Verify balance display
5. Check transaction history
6. Test dark mode toggle

## Features Detail

### Login (LoginActivity)
- Student ID authentication
- Token storage in encrypted preferences
- Auto-redirect to home if already logged in

### Home (HomeActivity)
- Large balance card display
- Pull-to-refresh functionality
- Navigate to transactions
- Navigate to settings

### Transactions (TransactionsActivity)
- RecyclerView list of transactions
- Expandable item details showing ItemsJson
- Auto-load on screen open

### Settings (SettingsActivity)
- Dark mode toggle (persisted)
- Logout with API call
- Clear secure storage

## Security

- Uses `EncryptedSharedPreferences` with AES256_GCM
- JWT tokens for API authentication
- Network traffic over HTTPS (configure in production)

## Dependencies

See `app/build.gradle.kts` for full list:
- AndroidX Core KTX
- Material Components
- Retrofit + Gson
- OkHttp Logging
- Security Crypto
- SwipeRefreshLayout
- RecyclerView
- Firebase Messaging

## License

Proprietary - Bangko ng Seton
