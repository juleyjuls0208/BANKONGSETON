# Building iOS IPA Without a Mac

This guide explains how to build an IPA (iOS app package) for sideloading without having a Mac computer.

## Overview

Building an IPA file requires:
1. **macOS environment** - Apple only allows iOS builds on Macs (or cloud CI/CD services)
2. **Apple Developer Account** ($99/year) - Required for device testing
3. **Code Signing Certificates** - Required to run on real devices
4. **Provisioning Profile** - Links certificate to your app bundle ID

Since you don't have a Mac, you have two main options:

### Option 1: Use Codemagic (Recommended - Free for Open Source)

[Codemagic](https://codemagic.io/) is a cloud-based CI/CD service that provides Mac build infrastructure. Free for open source projects.

**Setup Steps:**

1. **Create Codemagic Account**
   - Go to https://codemagic.io/
   - Sign up with GitHub/GitLab/Bitbucket
   - Connect your repository

2. **Import Your Project**
   - Click "Add new application"
   - Select your repository
   - Codemagic auto-detects `codemagic.yaml`

3. **Set Up Code Signing (for IPA builds)**

   First, get your Apple Developer credentials:

   a. **Create Apple Developer Account** (if not already)
      - Go to https://developer.apple.com
      - Enroll in the Apple Developer Program ($99/year)

   b. **Get Team ID**
      - Log into Apple Developer Portal
      - Go to Membership → Team ID

   c. **Create Certificates (requires a Mac temporarily)**
      
      If you have access to a Mac (friend's, university lab, etc.):
      ```
      1. Open Xcode → Preferences → Accounts
      2. Add your Apple ID
      3. Click "Manage Certificates"
      4. Click "+" → "Apple Development" (for development)
      5. Export: Xcode → Preferences → Accounts → Export Accounts
      6. Save as .developerprofile
      ```

      Without a Mac, you'll need to use **Codemagic's automatic signing**:
      
      ```
      Set environment variable: APPLE_APP_SPECIFIC_PASSWORD
      Set environment variable: APPLE_ID (your Apple ID email)
      Set environment variable: APPLE_TEAM_ID (from Apple Developer Portal)
      ```

   d. **Create Provisioning Profile (via Apple Developer Portal)**
      
      1. Go to https://developer.apple.com/profiles
      2. Click "+" to create new profile
      3. Select "iOS App Development"
      4. Choose your App ID (or create new)
      5. Select your certificate
      6. Choose devices (for development testing)
      7. Name and download the profile

4. **Configure Environment Variables in Codemagic**

   Go to your app settings → Environment variables:

   | Variable | Value |
   |----------|-------|
   | `APPLE_ID` | Your Apple Developer email |
   | `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password from Apple |
   | `APPLE_TEAM_ID` | Your Team ID (e.g., ABC123XYZ) |

5. **Store Certificates/Profiles (if using manual signing)**

   For manual signing, base64 encode your files:

   ```bash
   # On a Mac (or use online base64 encoder)
   base64 -i Certificates.p12 -o cert.b64
   
   # Set as Codemagic secret:
   # CERTIFICATE_DATA=<base64_content>
   # PROVISIONING_PROFILE_DATA=<base64_profile>
   ```

6. **Build and Download**

   - Trigger a build manually or push code
   - Wait for build to complete
   - Download the IPA from Artifacts

### Option 2: GitHub Actions with macOS Runner

GitHub provides macOS runners that can build iOS apps. Requires GitHub Pro or Teams plan.

**Setup Steps:**

1. **Store Secrets in GitHub**

   Go to your repo → Settings → Secrets and add:

   | Secret Name | Description |
   |-------------|-------------|
   | `CERTIFICATE_DATA` | Base64 encoded .p12 certificate |
   | `CERTIFICATE_PASSWORD` | Password for the certificate |
   | `PROVISIONING_PROFILE_DATA` | Base64 encoded .mobileprovision |
   | `APPLE_TEAM_ID` | Your Apple Team ID |

2. **Trigger IPA Build**

   - Go to Actions tab
   - Select "Build iOS IPA (Sideload)"
   - Click "Run workflow"
   - Select "sideload" from dropdown

3. **Download the IPA**

   - Wait for build (~15-30 minutes)
   - Download from workflow artifacts

### Option 3: Bitrise (Alternative CI/CD)

Bitrise is another cloud CI/CD service for iOS:

1. Sign up at https://bitrise.io/
2. Connect your repository
3. Configure code signing (similar to Codemagic)
4. Build and download

## Getting Certificates Without a Mac

### Option A: Use a Friend's Mac (Easiest)

1. Borrow a Mac for 15 minutes
2. Follow Apple's instructions to create certificates
3. Export them as .p12 files
4. Transfer files securely to your Windows machine
5. Use in your CI/CD service

### Option B: Automatic Signing via Codemagic/Bitrise

Services like Codemagic can handle code signing automatically:

1. Provide your Apple Developer credentials
2. The service creates certificates on your behalf
3. You get a provisioning profile to download

**Limitation:** App-specific password required (free to create)

### Option C: Use Transporter App (Mac required for initial upload)

If you have iTunes/Finder on Windows:
- You can sideload using Xcode on Windows via [Xcode on Windows alternatives](https://github.com/anders限额)

## Sideloading the IPA

Once you have the IPA file:

### Method 1: AltStore (Recommended - Free)

[AltStore](https://altstore.io/) allows sideloading apps on iOS without jailbreak.

1. **Install AltServer on Windows**
   - Download from https://altstore.io/
   - Install AltServer application

2. **Connect your iOS device**
   - Make sure your device is connected via USB
   - Trust the computer on your device

3. **Install AltStore on iOS**
   - Follow AltStore installation instructions
   - Use the AltServer menu to install AltStore to your device

4. **Sideload the IPA**
   - Click the AltServer icon in system tray
   - Select "Install AltStore" or "Install IPA"
   - Choose your IPA file
   - Wait for installation

### Method 2: 3uTools

1. Download 3uTools from https://www.3u.com/
2. Connect your iOS device
3. Go to "Toolbox" → "One-click Sideload"
4. Select your IPA file
5. Wait for installation

### Method 3: iTunes/Finder (Limited)

- Standard iTunes can install some apps
- Only works with properly signed IPAs
- Limited functionality

## Troubleshooting

### "No certificate found"
- Ensure certificates are properly imported
- Check certificate has not expired
- Verify team ID matches

### "Provisioning profile not found"
- Download and install the correct .mobileprovision file
- Ensure bundle ID matches the profile

### "Device not included in provisioning profile"
- Add your device UDID to the provisioning profile
- Create a new profile with your device

### "IPA build fails in CI/CD"
- Check build logs for specific errors
- Ensure environment variables are set correctly
- Verify code signing settings match

## Quick Reference

### Bundle ID
```
com.bankongseton.student
```

### Display Name
```
BankongSeton Student
```

### Minimum iOS Version
```
iOS 16.0
```

### Required Capabilities
- Push Notifications
- Camera (for QR scanning)
- NFC (for card reading)

## File Structure

```
mobile/ios/
├── codemagic.yaml          # Codemagic CI/CD configuration
├── BankongSetonStudent/
│   ├── BankongSetonStudent.xcodeproj/
│   ├── exportOptions.plist # IPA export settings template
│   ├── App/
│   ├── Core/
│   ├── Models/
│   ├── ViewModels/
│   ├── Views/
│   └── Assets.xcassets/
└── README.md (this file)
```

## Support

If you encounter issues:
1. Check Codemagic/Bitrise documentation
2. Review GitHub Actions logs
3. Verify Apple Developer Portal settings
4. Ensure all certificates are valid and not expired
