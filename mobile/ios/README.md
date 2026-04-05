# BankongSeton Student iOS App

A SwiftUI-based iOS app for students to manage their digital wallet, view balances, make QR payments, and track transactions.

## Project Structure

```
mobile/ios/
├── codemagic.yaml          # CI/CD configuration for cloud builds
├── BankongSetonStudent/
│   ├── BankongSetonStudent.xcodeproj/
│   ├── exportOptions.plist # IPA export settings template
│   ├── App/               # App entry point
│   ├── Core/              # Core utilities (Auth, Network, Keychain)
│   ├── Models/            # Data models
│   ├── ViewModels/        # MVVM ViewModels
│   ├── Views/             # SwiftUI Views
│   ├── UI/                # UI components and theming
│   └── Assets.xcassets/   # App assets
└── README.md
```

## Building Without a Mac

### Option 1: Codemagic (Recommended)

Codemagic provides free Mac build infrastructure for open source projects.

1. **Sign up at https://codemagic.io/**
2. **Connect your GitHub repository**
3. **Configure code signing:**
   - Add environment variables: `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID`
   - Or upload certificates manually for manual signing
4. **Push code** to trigger builds automatically
5. **Download IPA** from build artifacts

See [docs/BUILD_IPA_WITHOUT_MAC.md](../../docs/BUILD_IPA_WITHOUT_MAC.md) for detailed instructions.

### Option 2: GitHub Actions

GitHub Actions can build iOS apps using macOS runners.

1. **Add secrets to your repository:**
   - `CERTIFICATE_DATA` (base64 encoded .p12)
   - `CERTIFICATE_PASSWORD`
   - `PROVISIONING_PROFILE_DATA` (base64 encoded .mobileprovision)
   - `APPLE_TEAM_ID`
2. **Run the "Build iOS IPA (Sideload)" workflow**
3. **Download the IPA** from workflow artifacts

### Option 3: Bitrise

Bitrise is another cloud CI/CD option:
1. Sign up at https://bitrise.io/
2. Connect repository
3. Configure code signing
4. Build and download

## Sideloading the IPA

Once you have an IPA file:

### AltStore (Recommended - Free)
1. Install [AltStore](https://altstore.io/) on your Windows PC
2. Connect your iOS device via USB
3. Use AltServer to install AltStore to your iOS device
4. Sideload the IPA via AltStore

### 3uTools
1. Download [3uTools](https://www.3u.com/)
2. Connect your iOS device
3. Use "One-click Sideload" feature

## CI/CD Workflows

### Workflows Available

| Workflow | Purpose | Code Signing |
|----------|---------|---------------|
| `ios-student-app-sideload` | Build IPA for device testing | Required |
| `ios-student-app-simulator` | Build for simulator | Not required |

### Simulator Build (No Code Signing)
```bash
# Trigger automatically by pushing to main or gsd/* branches
git push origin main
```

### Device Build (Requires Code Signing)
1. Set up environment variables in Codemagic/GitHub
2. Manually trigger the sideload workflow

## Requirements

- **Bundle ID:** `com.bankongseton.student`
- **Display Name:** `BankongSeton Student`
- **Minimum iOS:** 16.0
- **Frameworks:** SwiftUI, Combine

## Features

- [x] Login with student credentials
- [x] View account balance
- [x] Transaction history
- [x] Budget management
- [x] QR code payment
- [x] QR code scanning
- [x] Lost card reporting
- [x] Settings management

## Development

### Local Development (requires Mac)
```bash
cd BankongSetonStudent
xcodebuild build -project BankongSetonStudent.xcodeproj -scheme BankongSetonStudent
```

### Code Quality Checks
The CI/CD pipeline runs:
- Philippine Peso symbol validation
- Deprecated NavigationView check
- Build verification

## License

Proprietary - BankongSeton
