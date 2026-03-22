import SwiftUI
import AVFoundation

struct QRScannerView: UIViewControllerRepresentable {
    var onCodeScanned: (String) -> Void
    var onScannerFailure: (String) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onCodeScanned: onCodeScanned, onScannerFailure: onScannerFailure)
    }

    func makeUIViewController(context: Context) -> ScannerViewController {
        let vc = ScannerViewController()
        vc.delegate = context.coordinator
        vc.onScannerFailure = context.coordinator.onScannerFailure
        return vc
    }

    func updateUIViewController(_ uiViewController: ScannerViewController, context: Context) {}

    // MARK: - Coordinator

    final class Coordinator: NSObject, AVCaptureMetadataOutputObjectsDelegate {
        var onCodeScanned: (String) -> Void
        var onScannerFailure: (String) -> Void

        init(
            onCodeScanned: @escaping (String) -> Void,
            onScannerFailure: @escaping (String) -> Void
        ) {
            self.onCodeScanned = onCodeScanned
            self.onScannerFailure = onScannerFailure
        }

        func metadataOutput(
            _ output: AVCaptureMetadataOutput,
            didOutput metadataObjects: [AVMetadataObject],
            from connection: AVCaptureConnection
        ) {
            guard let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
                  object.type == .qr,
                  let stringValue = object.stringValue else {
                return
            }

            DispatchQueue.main.async {
                self.onCodeScanned(stringValue)
            }
        }
    }
}

// MARK: - ScannerViewController

final class ScannerViewController: UIViewController {
    weak var delegate: AVCaptureMetadataOutputObjectsDelegate?
    var onScannerFailure: ((String) -> Void)?

    private var captureSession: AVCaptureSession?
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var hasReportedFailure = false

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        configureScanner()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        startCaptureSessionIfNeeded()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        stopCaptureSessionIfNeeded()
    }

    private func configureScanner() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            setupSession()

        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    if granted {
                        self?.setupSession()
                        self?.startCaptureSessionIfNeeded()
                    } else {
                        self?.reportScannerFailure(
                            "Camera access was denied. Enable Camera access in Settings, then tap Retry."
                        )
                    }
                }
            }

        case .denied:
            reportScannerFailure("Camera access is denied. Enable Camera access in Settings, then tap Retry.")

        case .restricted:
            reportScannerFailure("Camera access is restricted on this device. Use another device or ask for permission, then tap Retry.")

        @unknown default:
            reportScannerFailure("Camera setup failed due to an unknown permission state. Tap Retry.")
        }
    }

    private func setupSession() {
        let session = AVCaptureSession()

        guard let device = AVCaptureDevice.default(for: .video) else {
            reportScannerFailure("No camera is available on this device. Tap Retry or use another device.")
            return
        }

        guard let input = try? AVCaptureDeviceInput(device: device), session.canAddInput(input) else {
            reportScannerFailure("Failed to configure camera input. Tap Retry to try again.")
            return
        }
        session.addInput(input)

        let metadataOutput = AVCaptureMetadataOutput()
        guard session.canAddOutput(metadataOutput) else {
            reportScannerFailure("Failed to configure QR scanner output. Tap Retry to try again.")
            return
        }

        session.addOutput(metadataOutput)
        metadataOutput.setMetadataObjectsDelegate(delegate, queue: DispatchQueue.main)

        guard metadataOutput.availableMetadataObjectTypes.contains(.qr) else {
            reportScannerFailure("QR scanning is unavailable on this device. Tap Retry or use another device.")
            return
        }

        metadataOutput.metadataObjectTypes = [.qr]

        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)

        self.previewLayer = previewLayer
        self.captureSession = session
    }

    private func startCaptureSessionIfNeeded() {
        guard let captureSession, !captureSession.isRunning else { return }

        DispatchQueue.global(qos: .userInitiated).async {
            captureSession.startRunning()
        }
    }

    private func stopCaptureSessionIfNeeded() {
        guard let captureSession, captureSession.isRunning else { return }

        DispatchQueue.global(qos: .userInitiated).async {
            captureSession.stopRunning()
        }
    }

    private func reportScannerFailure(_ message: String) {
        guard !hasReportedFailure else { return }
        hasReportedFailure = true
        onScannerFailure?(message)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.layer.bounds
    }
}
