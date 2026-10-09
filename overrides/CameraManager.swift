// Based on TrackOSC CameraManager.swift, MIT, Copyright (c) 2026 Joel Gethin Lewis.
// EpicWin: physical rear-lens selection, transactional switching and status.
@preconcurrency import AVFoundation
import ImageIO
import os.lock

final class CameraManager: NSObject, @unchecked Sendable {
    let session = AVCaptureSession()
    let previewLayer: AVCaptureVideoPreviewLayer

    private let sessionQueue = DispatchQueue(label: "poseiosc.camera.session")
    private let videoQueue = DispatchQueue(label: "poseiosc.camera.video")
    private let output = AVCaptureVideoDataOutput()
    private var conveyor: FrameConveyor?
    // Camera state is only mutated on sessionQueue. Frame callbacks read facing
    // through a lock, not a property concurrently changed by configuration.
    private var position: AVCaptureDevice.Position = .back
    private var rearLens: CameraLens = .wide
    private var selectionDescription = "Starting camera"
    private let frontCamera = OSAllocatedUnfairLock<Bool>(initialState: false)
    private let autoAngle = OSAllocatedUnfairLock<Int32>(initialState: 90)
    private let orientationLock = OSAllocatedUnfairLock<CameraOrientationSetting>(initialState: .auto)

    override init() {
        previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        super.init()
    }

    func attach(conveyor: FrameConveyor) { self.conveyor = conveyor }

    func start(
        position requestedPosition: AVCaptureDevice.Position,
        lens: CameraLens,
        report: @escaping @Sendable (String) -> Void
    ) {
        sessionQueue.async { [self] in
            if session.inputs.isEmpty || position != requestedPosition || rearLens != lens {
                selectionDescription = configure(position: requestedPosition, lens: lens)
            }
            if !session.inputs.isEmpty && !session.isRunning { session.startRunning() }
            report(selectionDescription)
        }
    }

    func stop() {
        sessionQueue.async { [self] in
            if session.isRunning { session.stopRunning() }
        }
    }

    func setOrientationLock(_ setting: CameraOrientationSetting) {
        orientationLock.withLock { $0 = setting }
    }

    func setAutoInterfaceAngle(_ angle: Int32) { autoAngle.withLock { $0 = angle } }
    var effectiveAngle: Int32 { currentCaptureAngle() }

    private func configure(position newPosition: AVCaptureDevice.Position, lens: CameraLens) -> String {
        // Ultra-wide is a rear-camera choice only. Never try to find a front
        // ultra-wide device: that would break the existing selfie switch.
        let requestedType: AVCaptureDevice.DeviceType = newPosition == .back ? lens.deviceType : .builtInWideAngleCamera
        let requestedDevice = AVCaptureDevice.default(requestedType, for: .video, position: newPosition)
        let fallback = requestedDevice == nil && newPosition == .back && lens == .ultraWide
        guard let device = requestedDevice ?? (fallback
            ? AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: newPosition)
            : nil) else {
            return "Camera unavailable; previous camera retained"
        }
        let input: AVCaptureDeviceInput
        do { input = try AVCaptureDeviceInput(device: device) }
        catch { return "Camera input failed; check camera permission. Previous camera retained"
        }

        session.beginConfiguration()
        defer { session.commitConfiguration() }
        let oldInputs = session.inputs
        for oldInput in oldInputs { session.removeInput(oldInput) }
        guard session.canAddInput(input) else {
            for oldInput in oldInputs where session.canAddInput(oldInput) { session.addInput(oldInput) }
            return "Could not switch lens; previous camera retained"
        }
        session.addInput(input)
        if session.canSetSessionPreset(.hd1280x720) { session.sessionPreset = .hd1280x720 }
        if !session.outputs.contains(output) {
            output.alwaysDiscardsLateVideoFrames = true
            output.setSampleBufferDelegate(self, queue: videoQueue)
            guard session.canAddOutput(output) else {
                session.removeInput(input)
                for oldInput in oldInputs where session.canAddInput(oldInput) { session.addInput(oldInput) }
                return "Camera output unavailable; previous camera retained"
            }
            session.addOutput(output)
        }
        position = newPosition
        rearLens = lens
        frontCamera.withLock { $0 = newPosition == .front }

        if let connection = output.connection(with: .video) {
            if connection.isVideoMirroringSupported {
                connection.automaticallyAdjustsVideoMirroring = false
                connection.isVideoMirrored = false
            }
            if connection.isVideoStabilizationSupported { connection.preferredVideoStabilizationMode = .off }
            if connection.isCameraIntrinsicMatrixDeliverySupported { connection.isCameraIntrinsicMatrixDeliveryEnabled = true }
        }
        if let preview = previewLayer.connection, preview.isVideoMirroringSupported {
            preview.automaticallyAdjustsVideoMirroring = false
            preview.isVideoMirrored = false
        }
        if newPosition == .front { return "Front camera (rear lens choice saved)" }
        if fallback { return "0.5x unavailable - using rear 1x" }
        return "Rear \(lens.label) - \(device.localizedName)"
    }

    private func currentCaptureAngle() -> Int32 {
        let lock = orientationLock.withLock { $0 }
        return lock == .auto ? autoAngle.withLock { $0 } : Int32(lock.rawValue)
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let conveyor, let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let angle = currentCaptureAngle()
        let width = Int32(CVPixelBufferGetWidth(pixelBuffer))
        let height = Int32(CVPixelBufferGetHeight(pixelBuffer))
        let swapped = VisionAngle.isQuarterTurn(angle)
        conveyor.submit(FrameBox(
            sampleBuffer: sampleBuffer,
            pixelBuffer: pixelBuffer,
            orientation: VisionAngle.orientation(forDegrees: angle),
            orientedWidth: swapped ? height : width,
            orientedHeight: swapped ? width : height,
            rotationDegrees: angle,
            isFrontCamera: frontCamera.withLock { $0 }
        ))
    }
}
