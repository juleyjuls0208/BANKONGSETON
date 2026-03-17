---
estimated_steps: 8
estimated_files: 7
---

# T03: Build iOS QR views — AVFoundation scanner, confirmation, HomeView wiring, pbxproj registration

**Slice:** S04 — Android + iOS App QR Pay
**Milestone:** M005

## Description

Creates 4 new Swift files for iOS QR payment (`QRModels.swift`, `QRPayViewModel.swift`, `QRScannerView.swift`, `QRPayView.swift`), adds an always-visible "Pay with QR" button to `HomeView.swift`, and correctly registers all new files in `project.pbxproj`. Also adds `INFOPLIST_KEY_NSCameraUsageDescription` to the build settings (project uses `GENERATE_INFOPLIST_FILE = YES`, so there is no separate Info.plist).

**Prerequisite:** T01 must be complete — `APIClient.getQrCart(token:)`, `APIClient.confirmQrPayment(token:)`, `APIEndpoints.qrCart`, `APIEndpoints.qrConfirm`, and `AuthManager.login(token:student:jwtToken:)` must exist.

## Steps

1. **`Models/QRModels.swift`** — create new file with QR-specific model types:

   ```swift
   import Foundation

   // MARK: - QR Cart Models

   struct QrCartItem: Codable {
       let name: String
       let price: Double
       let qty: Int
   }

   struct QrCartResponse: Codable {
       let items: [QrCartItem]
       let total: Double
       let cashier: String
   }

   // MARK: - QR Confirm Models

   struct QrConfirmRequest: Codable {
       let token: String
   }

   struct QrConfirmResponse: Codable {
       let message: String
       let newBalance: Double?

       enum CodingKeys: String, CodingKey {
           case message
           case newBalance = "new_balance"
       }
   }
   ```

   Also add QR-specific error handling in `APIClient.swift` (T01 created `perform<T>` which returns `httpError(402)` for HTTP 402 — `QRPayViewModel` will branch on `APIError.httpError(402)` to show "insufficient balance").

2. **`ViewModels/QRPayViewModel.swift`** — create new file:

   ```swift
   import Foundation
   import SwiftUI

   enum QRPayState {
       case scanning
       case loading
       case confirming(cart: QrCartResponse, token: String)
       case success(newBalance: Double?)
       case error(String)
   }

   @MainActor
   final class QRPayViewModel: ObservableObject {
       @Published var state: QRPayState = .scanning
       @Published var isPresented: Bool = true

       func handleScannedURL(_ urlString: String, apiClient: APIClient) {
           // Extract token from URL last path segment
           guard let url = URL(string: urlString),
                 let token = url.pathComponents.last, !token.isEmpty,
                 urlString.contains("/api/qr/") else {
               return  // ignore non-QR URLs
           }
           state = .loading
           Task {
               do {
                   let cart = try await apiClient.getQrCart(token: token)
                   state = .confirming(cart: cart, token: token)
               } catch APIError.httpError(404), APIError.httpError(410) {
                   state = .error("QR code has expired. Ask the cashier to generate a new one.")
               } catch APIError.unauthorized {
                   state = .error("Session expired. Please log out and log in again.")
               } catch APIError.networkError(let e) {
                   state = .error("Network error: \(e.localizedDescription)")
               } catch {
                   state = .error("Failed to load cart. Please try again.")
               }
           }
       }

       func confirm(token: String, apiClient: APIClient) {
           state = .loading
           Task {
               do {
                   let response = try await apiClient.confirmQrPayment(token: token)
                   state = .success(newBalance: response.newBalance)
               } catch APIError.httpError(402) {
                   state = .error("Insufficient balance. Please top up your card.")
               } catch APIError.httpError(404), APIError.httpError(410) {
                   state = .error("QR code has expired. Ask the cashier to generate a new one.")
               } catch APIError.unauthorized {
                   state = .error("Session expired. Please log out and log in again.")
               } catch APIError.networkError(let e) {
                   state = .error("Network error: \(e.localizedDescription)")
               } catch {
                   state = .error("Payment failed. Please try again.")
               }
           }
       }

       func reset() {
           state = .scanning
       }
   }
   ```

3. **`Views/QR/QRScannerView.swift`** — create new file. Note: the `Views/QR/` directory does not exist yet — create it. This file uses `UIViewControllerRepresentable` wrapping `AVCaptureSession`:

   ```swift
   import SwiftUI
   import AVFoundation

   struct QRScannerView: UIViewControllerRepresentable {
       var onCodeScanned: (String) -> Void

       func makeCoordinator() -> Coordinator {
           Coordinator(onCodeScanned: onCodeScanned)
       }

       func makeUIViewController(context: Context) -> ScannerViewController {
           let vc = ScannerViewController()
           vc.delegate = context.coordinator
           return vc
       }

       func updateUIViewController(_ uiViewController: ScannerViewController, context: Context) {}

       // MARK: - Coordinator

       class Coordinator: NSObject, AVCaptureMetadataOutputObjectsDelegate {
           var onCodeScanned: (String) -> Void
           init(onCodeScanned: @escaping (String) -> Void) {
               self.onCodeScanned = onCodeScanned
           }

           func metadataOutput(
               _ output: AVCaptureMetadataOutput,
               didOutput metadataObjects: [AVMetadataObject],
               from connection: AVCaptureConnection
           ) {
               guard let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
                     object.type == .qr,
                     let stringValue = object.stringValue else { return }
               DispatchQueue.main.async {
                   self.onCodeScanned(stringValue)
               }
           }
       }
   }

   // MARK: - ScannerViewController

   protocol ScannerViewControllerDelegate: AnyObject {
       func metadataOutput(
           _ output: AVCaptureMetadataOutput,
           didOutput metadataObjects: [AVMetadataObject],
           from connection: AVCaptureConnection
       )
   }

   final class ScannerViewController: UIViewController {
       weak var delegate: AVCaptureMetadataOutputObjectsDelegate?
       private var captureSession: AVCaptureSession?
       private var previewLayer: AVCaptureVideoPreviewLayer?

       override func viewDidLoad() {
           super.viewDidLoad()
           view.backgroundColor = .black
           setupSession()
       }

       override func viewWillAppear(_ animated: Bool) {
           super.viewWillAppear(animated)
           DispatchQueue.global(qos: .userInitiated).async { [weak self] in
               self?.captureSession?.startRunning()
           }
       }

       override func viewWillDisappear(_ animated: Bool) {
           super.viewWillDisappear(animated)
           DispatchQueue.global(qos: .userInitiated).async { [weak self] in
               self?.captureSession?.stopRunning()
           }
       }

       private func setupSession() {
           let session = AVCaptureSession()
           guard let device = AVCaptureDevice.default(for: .video),
                 let input = try? AVCaptureDeviceInput(device: device),
                 session.canAddInput(input) else { return }
           session.addInput(input)

           let metadataOutput = AVCaptureMetadataOutput()
           guard session.canAddOutput(metadataOutput) else { return }
           session.addOutput(metadataOutput)
           metadataOutput.setMetadataObjectsDelegate(delegate, queue: DispatchQueue.main)
           if metadataOutput.availableMetadataObjectTypes.contains(.qr) {
               metadataOutput.metadataObjectTypes = [.qr]
           }

           let previewLayer = AVCaptureVideoPreviewLayer(session: session)
           previewLayer.frame = view.layer.bounds
           previewLayer.videoGravity = .resizeAspectFill
           view.layer.addSublayer(previewLayer)
           self.previewLayer = previewLayer

           captureSession = session
       }

       override func viewDidLayoutSubviews() {
           super.viewDidLayoutSubviews()
           previewLayer?.frame = view.layer.bounds
       }
   }
   ```

4. **`Views/QR/QRPayView.swift`** — create new file:

   ```swift
   import SwiftUI

   struct QRPayView: View {
       @EnvironmentObject var apiClient: APIClient
       @StateObject private var viewModel = QRPayViewModel()
       @Environment(\.dismiss) private var dismiss
       private var onSuccess: (() -> Void)?

       init(onSuccess: (() -> Void)? = nil) {
           self.onSuccess = onSuccess
       }

       var body: some View {
           NavigationStack {
               Group {
                   switch viewModel.state {
                   case .scanning:
                       scanningView

                   case .loading:
                       VStack(spacing: 16) {
                           ProgressView()
                           Text("Loading cart…")
                               .foregroundColor(.secondary)
                       }
                       .frame(maxWidth: .infinity, maxHeight: .infinity)

                   case .confirming(let cart, let token):
                       confirmView(cart: cart, token: token)

                   case .success(let newBalance):
                       successView(newBalance: newBalance)

                   case .error(let message):
                       errorView(message: message)
                   }
               }
               .navigationTitle("Pay with QR")
               .navigationBarTitleDisplayMode(.inline)
               .toolbar {
                   ToolbarItem(placement: .cancellationAction) {
                       Button("Cancel") { dismiss() }
                   }
               }
           }
       }

       // MARK: Scanning

       private var scanningView: some View {
           ZStack(alignment: .bottom) {
               QRScannerView { scannedURL in
                   viewModel.handleScannedURL(scannedURL, apiClient: apiClient)
               }
               .ignoresSafeArea()

               Text("Point camera at QR code on terminal")
                   .foregroundColor(.white)
                   .padding(.horizontal, 16)
                   .padding(.vertical, 10)
                   .background(Color.black.opacity(0.6))
                   .cornerRadius(8)
                   .padding(.bottom, 48)
           }
       }

       // MARK: Confirmation

       private func confirmView(cart: QrCartResponse, token: String) -> some View {
           ScrollView {
               VStack(alignment: .leading, spacing: 20) {
                   VStack(alignment: .leading, spacing: 4) {
                       Text("Confirm Payment")
                           .font(.title2).bold()
                       Text("Cashier: \(cart.cashier)")
                           .font(.subheadline)
                           .foregroundColor(.secondary)
                   }
                   .padding(.top, 8)

                   Divider()

                   ForEach(cart.items, id: \.name) { item in
                       HStack {
                           Text(item.name)
                               .frame(maxWidth: .infinity, alignment: .leading)
                           Text("×\(item.qty)")
                               .foregroundColor(.secondary)
                               .frame(width: 40)
                           Text("₱\(String(format: "%.2f", item.price * Double(item.qty)))")
                               .frame(width: 80, alignment: .trailing)
                       }
                       .font(.subheadline)
                   }

                   Divider()

                   HStack {
                       Text("Total").font(.headline)
                       Spacer()
                       Text("₱\(String(format: "%.2f", cart.total))")
                           .font(.headline)
                           .foregroundColor(.accentColor)
                   }

                   VStack(spacing: 12) {
                       Button(action: { viewModel.confirm(token: token, apiClient: apiClient) }) {
                           Text("Pay Now")
                               .frame(maxWidth: .infinity)
                               .padding()
                               .background(Color.accentColor)
                               .foregroundColor(.white)
                               .cornerRadius(12)
                       }
                       Button(action: { dismiss() }) {
                           Text("Cancel")
                               .frame(maxWidth: .infinity)
                               .padding()
                               .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.accentColor))
                       }
                   }
                   .padding(.top, 8)
               }
               .padding()
           }
       }

       // MARK: Success

       private func successView(newBalance: Double?) -> some View {
           VStack(spacing: 20) {
               Image(systemName: "checkmark.circle.fill")
                   .font(.system(size: 64))
                   .foregroundColor(.green)
               Text("Payment Successful!")
                   .font(.title2).bold()
               if let balance = newBalance {
                   Text("New balance: ₱\(String(format: "%.2f", balance))")
                       .foregroundColor(.secondary)
               }
               Button("Done") {
                   onSuccess?()
                   dismiss()
               }
               .buttonStyle(.borderedProminent)
           }
           .frame(maxWidth: .infinity, maxHeight: .infinity)
           .onAppear {
               // Auto-dismiss success after 3 seconds
               DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                   onSuccess?()
                   dismiss()
               }
           }
       }

       // MARK: Error

       private func errorView(message: String) -> some View {
           VStack(spacing: 20) {
               Image(systemName: "exclamationmark.circle.fill")
                   .font(.system(size: 64))
                   .foregroundColor(.red)
               Text("Payment Error")
                   .font(.title2).bold()
               Text(message)
                   .multilineTextAlignment(.center)
                   .foregroundColor(.secondary)
               Button("Close") { dismiss() }
                   .buttonStyle(.borderedProminent)
           }
           .padding()
           .frame(maxWidth: .infinity, maxHeight: .infinity)
       }
   }
   ```

5. **`Views/Home/HomeView.swift`** — add "Pay with QR" button. Inside the `VStack(spacing: 24)` after the Balance Card section, add a QR pay button before the error message block (or just below the balance card). The cleanest placement is a new quick-action row directly under the balance card:

   ```swift
   // After the balance card VStack, before the error message
   Button(action: { showQrPay = true }) {
       Label("Pay with QR", systemImage: "qrcode.viewfinder")
           .frame(maxWidth: .infinity)
           .padding(.vertical, 14)
           .background(Color.accentColor)
           .foregroundColor(.white)
           .cornerRadius(14)
           .padding(.horizontal)
   }
   .sheet(isPresented: $showQrPay) {
       QRPayView {
           // On success, refresh balance
           Task { await viewModel.load(apiClient: apiClient, authManager: authManager) }
       }
       .environmentObject(apiClient)
   }
   ```

   Add `@State private var showQrPay = false` to the `HomeView` struct body (alongside any existing `@State` vars). If there are no existing `@State` vars, add it before the `var body: some View` line.

6. **`BankongSetonStudent.xcodeproj/project.pbxproj`** — add 4 new Swift files. The existing pattern uses `AA000001`–`AA000025` for `PBXBuildFile` and `BB000001`–`BB000025` for `PBXFileReference`. Next free IDs: `AA000026`–`AA000029` (build files) and `BB000026`–`BB000029` (file references).

   **Assignment:**
   - `QRModels.swift`: buildFile `AA000026`, fileRef `BB000026`
   - `QRPayViewModel.swift`: buildFile `AA000027`, fileRef `BB000027`
   - `QRScannerView.swift`: buildFile `AA000028`, fileRef `BB000028`
   - `QRPayView.swift`: buildFile `AA000029`, fileRef `BB000029`

   **A. PBXBuildFile section** — after line `AA000025 /* Assets.xcassets in Resources */`:
   ```
   		AA000026 /* QRModels.swift in Sources */ = {isa = PBXBuildFile; fileRef = BB000026 /* QRModels.swift */; };
   		AA000027 /* QRPayViewModel.swift in Sources */ = {isa = PBXBuildFile; fileRef = BB000027 /* QRPayViewModel.swift */; };
   		AA000028 /* QRScannerView.swift in Sources */ = {isa = PBXBuildFile; fileRef = BB000028 /* QRScannerView.swift */; };
   		AA000029 /* QRPayView.swift in Sources */ = {isa = PBXBuildFile; fileRef = BB000029 /* QRPayView.swift */; };
   ```

   **B. PBXFileReference section** — after `BB000025 /* Assets.xcassets */`:
   ```
   		BB000026 /* QRModels.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = QRModels.swift; sourceTree = "<group>"; };
   		BB000027 /* QRPayViewModel.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = QRPayViewModel.swift; sourceTree = "<group>"; };
   		BB000028 /* QRScannerView.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = QRScannerView.swift; sourceTree = "<group>"; };
   		BB000029 /* QRPayView.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = QRPayView.swift; sourceTree = "<group>"; };
   ```

   **C. PBXGroup for Models (EE000007)** — add `BB000026 /* QRModels.swift */` to the children list of the `EE000007 /* Models */` group.

   **D. PBXGroup for ViewModels (EE000008)** — add `BB000027 /* QRPayViewModel.swift */` to the children list of the `EE000008 /* ViewModels */` group.

   **E. New PBXGroup for Views/QR** — add a new group `EE000017 /* QR */` inside `EE000009 /* Views */` (alongside `EE000010` through `EE000016`):
   ```
   		EE000017 /* QR */ = {
   			isa = PBXGroup;
   			children = (
   				BB000028 /* QRScannerView.swift */,
   				BB000029 /* QRPayView.swift */,
   			);
   			path = QR;
   			sourceTree = "<group>";
   		};
   ```
   Add `EE000017 /* QR */,` to the children of `EE000009 /* Views */`.

   **F. PBXSourcesBuildPhase (FF000002)** — add all 4 new files to the `files` array:
   ```
   				AA000026 /* QRModels.swift in Sources */,
   				AA000027 /* QRPayViewModel.swift in Sources */,
   				AA000028 /* QRScannerView.swift in Sources */,
   				AA000029 /* QRPayView.swift in Sources */,
   ```

   **G. Camera usage description** — in both `FF000013 /* Debug (target) */` and `FF000014 /* Release (target) */` build settings (in the `XCBuildConfiguration` section), add:
   ```
   				INFOPLIST_KEY_NSCameraUsageDescription = "Bangko ng Seton uses the camera to scan QR codes for payment.";
   ```
   This works because the project has `GENERATE_INFOPLIST_FILE = YES` — Xcode reads `INFOPLIST_KEY_*` build settings as Info.plist entries at build time.

7. **Create the `Views/QR/` directory** — the physical directory must exist for Xcode to find the files:
   ```
   mkdir -p mobile/ios/BankongSetonStudent/Views/QR
   ```
   Write `QRScannerView.swift` to `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` and `QRPayView.swift` to `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`.

## Must-Haves

- [ ] `Models/QRModels.swift` exists with `QrCartItem`, `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse`
- [ ] `ViewModels/QRPayViewModel.swift` exists; handles all 5 `QRPayState` cases; correctly handles `httpError(402)` for insufficient funds
- [ ] `Views/QR/QRScannerView.swift` exists; uses `AVCaptureMetadataOutput` with `AVMetadataObjectTypeQRCode` (`.qr`); starts/stops session on `viewWillAppear`/`viewWillDisappear`
- [ ] `Views/QR/QRPayView.swift` exists; presents scanner as full-screen; switches to confirmation view on cart load; shows specific error messages for 402/404/410
- [ ] `HomeView.swift` has "Pay with QR" button that is always visible (no NFC availability check)
- [ ] `project.pbxproj` has entries `AA000026`–`AA000029` in `PBXBuildFile`; `BB000026`–`BB000029` in `PBXFileReference`; `EE000017` QR group; all 4 new source files in `PBXSourcesBuildPhase`
- [ ] `project.pbxproj` has `INFOPLIST_KEY_NSCameraUsageDescription` in both Debug and Release target build configs

## Verification

```bash
# QRPayView imported in HomeView
grep -q 'QRPayView\|showQrPay' mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift && echo "OK: QRPayView in HomeView"

# AVCaptureMetadataOutput in QRScannerView
grep -q 'AVCaptureMetadataOutput' mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift && echo "OK: QRScannerView uses AVFoundation"

# pbxproj has AA000026
grep -q 'AA000026' mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj && echo "OK: new IDs in pbxproj"

# QRModels.swift exists
test -f mobile/ios/BankongSetonStudent/Models/QRModels.swift && echo "OK: QRModels.swift exists"

# Camera usage description in pbxproj
grep -q 'NSCameraUsageDescription' mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj && echo "OK: camera usage description"
```

## Inputs

- T01 output: `APIClient.getQrCart(token:)`, `APIClient.confirmQrPayment(token:)`, `APIEndpoints.qrCart`, `APIEndpoints.qrConfirm` all exist
- `Views/Home/HomeView.swift` — current contents (add `@State private var showQrPay`; add QRPayView sheet)
- `BankongSetonStudent.xcodeproj/project.pbxproj` — current state; last used IDs are `AA000025`/`BB000025`; groups `EE000007`–`EE000016`; `FF000002` sources build phase; `FF000013`/`FF000014` target build configs

## Expected Output

- `Models/QRModels.swift` — 4 QR model structs
- `ViewModels/QRPayViewModel.swift` — `@MainActor ObservableObject` with `QRPayState` enum and two async methods
- `Views/QR/QRScannerView.swift` — `UIViewControllerRepresentable` with AVFoundation camera + QR scanning
- `Views/QR/QRPayView.swift` — SwiftUI view orchestrating scan → load → confirm → success/error states
- `Views/Home/HomeView.swift` — "Pay with QR" button + sheet presentation
- `project.pbxproj` — 4 new PBXBuildFile + 4 new PBXFileReference + 1 new PBXGroup (EE000017) + 4 entries in PBXSourcesBuildPhase + camera usage description in both target build configs
