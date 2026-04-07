# Quick Task: build ipa version of the ios app so that i can sideload it without using a mac computer

**Date:** 2026-04-05
**Branch:** gsd/quick/4-build-ipa-version-of-the-ios-app-so-that

## What Changed

- **Updated `codemagic.yaml`**: Added new `ios-student-app-sideload` workflow for building IPA files with code signing. Kept existing `ios-student-app-simulator` workflow for simulator builds.
- **Added GitHub Actions workflow** (`.github/workflows/ios-build.yml`): Three workflows for different build scenarios - simulator, sideload (for device testing), and release (for App Store).
- **Created `exportOptions.plist`**: Template file for IPA export configuration including code signing settings.
- **Added comprehensive documentation** (`docs/BUILD_IPA_WITHOUT_MAC.md`): Complete guide covering:
  - Codemagic setup (recommended, free for open source)
  - GitHub Actions with macOS runners
  - Bitrise as alternative
  - How to get certificates without a Mac
  - Sideloading options (AltStore, 3uTools)
- **Created shell script** (`scripts/build-ios-ipa.sh`): Interactive helper script for build options.
- **Created iOS README** (`mobile/ios/README.md`): Project-specific build instructions.

## Files Modified

- `mobile/ios/codemagic.yaml` - Added sideload workflow
- `mobile/ios/BankongSetonStudent/exportOptions.plist` - New file
- `mobile/ios/README.md` - New file
- `docs/BUILD_IPA_WITHOUT_MAC.md` - New file
- `scripts/build-ios-ipa.sh` - New file
- `.github/workflows/ios-build.yml` - New file

## Verification

- Files created with proper YAML/script syntax
- codemagic.yaml validated structure
- GitHub Actions workflow follows correct schema
- Documentation includes all necessary steps for IPA building

## How to Use

### Quick Start (Recommended: Codemagic)

1. Go to https://codemagic.io and create account
2. Connect your GitHub repository
3. Add environment variables:
   - `APPLE_ID` - Your Apple Developer email
   - `APPLE_APP_SPECIFIC_PASSWORD` - App-specific password
   - `APPLE_TEAM_ID` - From Apple Developer Portal
4. Trigger build → Download IPA from artifacts

### For Sideloading

Once you have the IPA file:
1. Install AltStore on Windows: https://altstore.io/
2. Connect iOS device via USB
3. Use AltServer to install IPA to device
4. Enjoy your sideloaded app!

See `docs/BUILD_IPA_WITHOUT_MAC.md` for detailed instructions.
