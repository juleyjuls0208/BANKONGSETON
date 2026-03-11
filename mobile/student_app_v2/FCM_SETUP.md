# Firebase Cloud Messaging (FCM) Setup Guide

## Step 1: Create Firebase Project

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com/
   - Click "Add project" or select existing project

2. **Add Project Details**
   - Project name: `Bangko ng Seton`
   - Google Analytics: Optional (can disable for now)
   - Click "Create project"

## Step 2: Add Android App to Firebase

1. **Register Your App**
   - In Firebase Console, click on Android icon
   - Android package name: `com.bankongseton.student`
   - App nickname (optional): `Student App`
   - Debug signing certificate SHA-1 (optional for now)
   - Click "Register app"

2. **Get SHA-1 Certificate (Optional but Recommended)**
   
   In Android Studio:
   ```
   View -> Tool Windows -> Gradle
   Navigate to: app -> Tasks -> android -> signingReport
   Double-click signingReport
   ```
   
   Or in command line:
   ```bash
   cd mobile/student_app_v2
   gradlew signingReport
   ```
   
   Copy the SHA-1 from debug keystore and add to Firebase.

## Step 3: Download google-services.json

1. **Download Configuration File**
   - Click "Download google-services.json"
   - This file contains your Firebase project configuration

2. **Place the File**
   - Move `google-services.json` to:
   ```
   L:\Louis\Desktop\BANKONGSETON\mobile\student_app_v2\app\google-services.json
   ```
   
   **IMPORTANT:** Must be in the `app/` directory, NOT in `app/src/`!

3. **Verify File Structure**
   ```
   mobile/student_app_v2/
   ├── app/
   │   ├── google-services.json  ← HERE!
   │   ├── build.gradle.kts
   │   └── src/
   └── build.gradle.kts
   ```

## Step 4: Enable Firebase Cloud Messaging

1. **In Firebase Console**
   - Go to Project Settings (gear icon)
   - Select "Cloud Messaging" tab
   - Note your **Server Key** and **Sender ID** (not needed in app, but good to save)

2. **Enable Cloud Messaging API**
   - Click "Manage API in Google Cloud Console"
   - Enable "Cloud Messaging API" if not already enabled

## Step 5: Verify Gradle Configuration

Your `app/build.gradle.kts` should already have these (already added):

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.gms.google-services")  // ← This line
}

dependencies {
    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
    implementation("com.google.firebase:firebase-messaging-ktx")
}
```

Your root `build.gradle.kts` should have (already added):

```kotlin
plugins {
    id("com.google.gms.google-services") version "4.4.0" apply false
}
```

## Step 6: Test FCM in App

1. **Build and Install App**
   ```
   Build -> Build Bundle(s) / APK(s) -> Build APK(s)
   ```

2. **Login to App**
   - App will automatically get FCM token
   - Token is saved in SecureStorage
   - Token is sent to backend on next login

3. **Verify Token Registration**
   - Check Android Studio Logcat for:
   ```
   FCM Token: <your-token-here>
   ```

4. **Test Notification from Firebase Console**
   - Go to Firebase Console -> Cloud Messaging
   - Click "Send your first message"
   - Notification title: "Test"
   - Notification text: "Hello from Firebase!"
   - Click "Send test message"
   - Paste your FCM token
   - Click "Test"

## Step 7: Backend FCM Token Storage

The app automatically sends the FCM token to your backend:

**When:** After successful login  
**Endpoint:** `POST /api/students/fcm-token`  
**Payload:**
```json
{
  "fcm_token": "device-firebase-token-here"
}
```

The backend stores this in Google Sheets `Users` sheet, `FCMToken` column.

## Troubleshooting

### google-services.json Not Found
- Error: `File google-services.json is missing`
- Solution: Make sure file is in `app/` directory (not `app/src/`)

### FCM Token is null
- Check: Firebase dependency is added
- Check: google-services.json is in correct location
- Check: Internet permission in AndroidManifest.xml
- Try: Clean and rebuild project

### Notifications Not Received
- Check: POST_NOTIFICATIONS permission granted (Android 13+)
- Check: App is not in battery optimization
- Check: FCM token was sent to backend
- Check: Server key is correct in backend notification sender

### Build Error: Google Services Plugin
- Solution: Make sure both `build.gradle.kts` files have the plugin declared
- Root level: `id("com.google.gms.google-services") version "4.4.0" apply false`
- App level: `id("com.google.gms.google-services")`

## What Happens Behind the Scenes

1. **On App Install:**
   - Firebase SDK generates unique FCM token for device
   - Token is stored in SecureStorage

2. **On Login:**
   - App retrieves FCM token from SecureStorage
   - Sends token to backend API
   - Backend stores in Google Sheets

3. **When Backend Sends Notification:**
   - Backend uses FCM Server Key to send notification
   - Firebase routes notification to correct device using token
   - FCMService in app receives notification
   - Notification is displayed in system tray

4. **Token Refresh:**
   - Firebase may refresh token periodically
   - FCMService.onNewToken() is called
   - New token is saved and will be sent on next login

## Security Notes

- ✅ FCM token is not sensitive data (safe to store in Sheets)
- ✅ Token is device-specific, not user-specific
- ✅ Token expires when app is uninstalled
- ❌ Never commit google-services.json to public repositories
- ❌ Never expose Server Key in client code

## Quick Reference

**Package Name:** `com.bankongseton.student`  
**google-services.json Location:** `app/google-services.json`  
**FCM Service Class:** `com.bankongseton.student.FCMService`  
**Token Storage:** `SecureStorage.kt` via EncryptedSharedPreferences  
**Backend Endpoint:** `POST /api/students/fcm-token`

---

**Next Step:** Update BASE_URL in ApiClient.kt (see BASE_URL_SETUP.md)
