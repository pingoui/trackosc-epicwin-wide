// EpicWin extension to TrackOSC. Camera choice does not change the OSC protocol.
import AVFoundation

enum CameraLens: String, CaseIterable, Identifiable, Sendable {
    case wide
    case ultraWide

    var id: String { rawValue }
    var label: String { self == .wide ? "1x" : "0.5x" }
    var deviceType: AVCaptureDevice.DeviceType {
        self == .wide ? .builtInWideAngleCamera : .builtInUltraWideCamera
    }

    static var ultraWideAvailable: Bool {
        AVCaptureDevice.default(.builtInUltraWideCamera, for: .video, position: .back) != nil
    }
}
