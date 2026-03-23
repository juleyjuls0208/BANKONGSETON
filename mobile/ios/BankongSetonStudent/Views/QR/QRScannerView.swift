import SwiftUI
import AVFoundation

struct QRScannerView: UIViewControllerRepresentable {
    var onCodeScanned: (String) -> Void
    var onError: (String) -> Void = { _ in }

    func makeUIViewController(context: Context) -> ScannerViewController {
        let vc = ScannerViewController()
        vc.onCodeScanned = onCodeScanned
        vc.onError = onError
        return vc
    }

    func updateUIViewController(_ uiViewController: ScannerViewController, context: Context) {}
}

final class ScannerViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    var onCodeScanned: ((String) -> Void)?
    var onError: ((String) -> Void)?

    private var captureSession: AVCaptureSession?
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var hasReportedError = false

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        configureCameraPermission()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        startSessionIfPossible()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.captureSession?.stopRunning()
        }
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.layer.bounds
    }

    private func configureCameraPermission() {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        switch status {
        case .authorized:
            setupSessionIfNeeded()

        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    guard let self else { return }
                    if granted {
                        self.setupSessionIfNeeded()
                    } else {
                        self.reportError("Camera access is denied. Enable camera permission in Settings.")
                    }
                }
            }

        case .denied, .restricted:
            reportError("Camera access is denied. Enable camera permission in Settings.")

        @unknown default:
            reportError("Camera permission state is unavailable. Please retry.")
        }
    }

    private func setupSessionIfNeeded() {
        guard captureSession == nil else {
            startSessionIfPossible()
            return
        }

        let session = AVCaptureSession()

        guard let device = AVCaptureDevice.default(for: .video) else {
            reportError("Camera is unavailable on this device.")
            return
        }

        do {
            let input = try AVCaptureDeviceInput(device: device)
            guard session.canAddInput(input) else {
                reportError("Unable to attach camera input. Please retry.")
                return
            }
            session.addInput(input)
        } catch {
            reportError("Unable to access camera. Please retry or check Settings.")
            return
        }

        let metadataOutput = AVCaptureMetadataOutput()
        guard session.canAddOutput(metadataOutput) else {
            reportError("Unable to configure QR scanner output. Please retry.")
            return
        }
        session.addOutput(metadataOutput)
        metadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)

        guard metadataOutput.availableMetadataObjectTypes.contains(.qr) else {
            reportError("QR scanning is not supported on this device.")
            return
        }
        metadataOutput.metadataObjectTypes = [.qr]

        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        previewLayer.frame = view.layer.bounds
        view.layer.addSublayer(previewLayer)

        self.captureSession = session
        self.previewLayer = previewLayer
        startSessionIfPossible()
    }

    private func startSessionIfPossible() {
        guard let captureSession else { return }
        guard !captureSession.isRunning else { return }

        DispatchQueue.global(qos: .userInitiated).async {
            captureSession.startRunning()
        }
    }

    private func reportError(_ message: String) {
        guard !hasReportedError else { return }
        hasReportedError = true
        DispatchQueue.main.async { [weak self] in
            self?.onError?(message)
        }
    }

    func metadataOutput(
        _ output: AVCaptureMetadataOutput,
        didOutput metadataObjects: [AVMetadataObject],
        from connection: AVCaptureConnection
    ) {
        guard let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
              object.type == .qr,
              let value = object.stringValue,
              !value.isEmpty else {
            return
        }

        captureSession?.stopRunning()
        onCodeScanned?(value)
    }
}
