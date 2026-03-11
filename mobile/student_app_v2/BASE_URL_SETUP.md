# API Base URL Configuration Guide

## What is BASE_URL?

The `BASE_URL` is the network address of your backend API server. The mobile app needs to know where to send API requests.

## File to Edit

**Location:** `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt`

**Current Line (around line 25):**
```kotlin
private const val BASE_URL = "http://192.168.68.122:5001/api/"
```

## How to Find Your Server IP Address

### Option 1: Check Backend Server Output

When you start your backend API server, it shows the IP:

```bash
cd backend/api
python api_server.py
```

Look for output like:
```
 * Running on http://192.168.1.100:5001
 * Running on http://192.168.68.122:5001
```

### Option 2: Windows - ipconfig

1. Open Command Prompt
2. Run: `ipconfig`
3. Look for "IPv4 Address" under your active network adapter:
   ```
   Wireless LAN adapter Wi-Fi:
      IPv4 Address. . . . . . . . . . . : 192.168.1.100
   ```

### Option 3: Check Router Admin Page

1. Open browser and go to your router (usually http://192.168.1.1)
2. Login to router admin
3. Look for "Connected Devices" or "DHCP Client List"
4. Find your computer's name and note the IP address

## Configuration Examples

### Example 1: Same WiFi Network (Most Common)

If your phone and computer are on the same WiFi:

```kotlin
private const val BASE_URL = "http://192.168.1.100:5001/api/"
```

**Replace `192.168.1.100` with YOUR computer's IP address**

**Important Notes:**
- ✅ Use `http://` (not `https://`) for local development
- ✅ Include the port `:5001`
- ✅ Include `/api/` at the end
- ❌ Don't use `localhost` - won't work from phone
- ❌ Don't use `127.0.0.1` - won't work from phone

### Example 2: Testing with Android Emulator

If using Android Studio Emulator on the same computer:

```kotlin
private const val BASE_URL = "http://10.0.2.2:5001/api/"
```

**Special Address:** `10.0.2.2` in emulator refers to `localhost` on host machine

### Example 3: Production Server

If you have a production server with domain:

```kotlin
private const val BASE_URL = "https://api.bankongseton.com/api/"
```

**Note:** Use `https://` for production!

## Step-by-Step Setup

### Step 1: Find Your IP

Run in PowerShell:
```powershell
(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi").IPAddress
```

Or Command Prompt:
```cmd
ipconfig | findstr "IPv4"
```

### Step 2: Start Backend Server

```bash
cd L:\Louis\Desktop\BANKONGSETON\backend\api
python api_server.py
```

Verify it's running and note the IP from the output.

### Step 3: Update ApiClient.kt

1. Open: `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt`

2. Find line ~25:
   ```kotlin
   private const val BASE_URL = "http://192.168.68.122:5001/api/"
   ```

3. Replace with YOUR IP:
   ```kotlin
   private const val BASE_URL = "http://YOUR_IP_HERE:5001/api/"
   ```

4. Save the file

### Step 4: Rebuild App

In Android Studio:
```
Build -> Clean Project
Build -> Rebuild Project
```

Or from terminal:
```bash
cd mobile/student_app_v2
gradlew clean
gradlew assembleDebug
```

### Step 5: Test Connection

1. Install and run the app
2. Try to login with a Student ID
3. Check Android Studio Logcat for network requests

**Look for:**
```
D/OkHttp: --> POST http://192.168.1.100:5001/api/auth/login
D/OkHttp: <-- 200 OK (123ms)
```

## Troubleshooting

### Error: "Unable to resolve host"

**Problem:** Phone can't find the server

**Solutions:**
1. Make sure computer and phone are on SAME WiFi network
2. Verify IP address is correct
3. Check computer firewall isn't blocking port 5001
4. Make sure backend server is actually running

### Error: "Connection refused"

**Problem:** Server is not listening on that IP/port

**Solutions:**
1. Verify backend server is running: `python api_server.py`
2. Check the port number is 5001
3. Try accessing in browser: `http://YOUR_IP:5001/api/health`

### Error: "Timeout"

**Problem:** Network is slow or server is not responding

**Solutions:**
1. Check WiFi signal strength
2. Restart backend server
3. Increase timeout in ApiClient.kt:
   ```kotlin
   .connectTimeout(30, TimeUnit.SECONDS)
   .readTimeout(30, TimeUnit.SECONDS)
   ```

### Error: "Cleartext traffic not permitted"

**Problem:** Android blocking HTTP (non-HTTPS) connections

**Solution:** Already configured in AndroidManifest.xml:
```xml
android:usesCleartextTraffic="true"
```

If still blocked, add to AndroidManifest.xml:
```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

Create `res/xml/network_security_config.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">192.168.1.100</domain>
    </domain-config>
</network-security-config>
```

## Testing API Connection Before Building App

### Test 1: From Computer Browser

Open browser and go to:
```
http://YOUR_IP:5001/api/health
```

Should return: `{"status": "healthy"}`

### Test 2: From Phone Browser

1. Connect phone to same WiFi
2. Open browser on phone
3. Go to: `http://YOUR_IP:5001/api/health`
4. Should see: `{"status": "healthy"}`

**If this works, your app will work too!**

## Production Deployment

For production, you'll need:

1. **Domain Name**
   ```kotlin
   private const val BASE_URL = "https://api.bankongseton.com/api/"
   ```

2. **SSL Certificate**
   - Use Let's Encrypt (free)
   - Or cloud provider SSL

3. **Remove usesCleartextTraffic**
   ```xml
   android:usesCleartextTraffic="false"
   ```

4. **Update Security Config**
   - Remove cleartext exceptions
   - Add certificate pinning (optional)

## Quick Reference

| Environment | BASE_URL Example |
|-------------|------------------|
| Local WiFi (Phone) | `http://192.168.1.100:5001/api/` |
| Android Emulator | `http://10.0.2.2:5001/api/` |
| Production | `https://api.bankongseton.com/api/` |

**Current Backend Port:** 5001  
**Protocol:** HTTP (local), HTTPS (production)  
**Path:** `/api/` (always include trailing slash)

---

**Next Step:** Build and install the app on your phone!
