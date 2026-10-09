"""Reproducible build-time overlay; refuses unknown/already patched source trees."""
from pathlib import Path
import argparse
import hashlib
import json

KIT = Path(__file__).resolve().parent


def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f"{label}: expected exactly one upstream anchor; refusing partial patch")
    return text.replace(old, new, 1)


def patched_sources(root):
    """Prepare everything before writing any changes. Easy to unit-test on Windows."""
    files = {}
    for name in ("SettingsStore.swift", "AppModel.swift", "Views/SettingsView.swift",
                 "Views/ControlBarView.swift", "Views/ContentView.swift"):
        files[name] = (root / "Sender" / name).read_text(encoding="utf-8")

    s = files["SettingsStore.swift"]
    s = replace_once(s, "    var cameraOrientation: CameraOrientationSetting {", '''    var rearCameraLens: CameraLens {
        didSet { defaults.set(rearCameraLens.rawValue, forKey: "epicwinRearLens") }
    }
    var keepScreenAwake: Bool {
        didSet { defaults.set(keepScreenAwake, forKey: "epicwinKeepScreenAwake") }
    }

    var cameraOrientation: CameraOrientationSetting {''', "settings properties")
    s = replace_once(s, "        enabledDetectors = Detector.loadEnabled(from: defaults)", '''        // This separate app starts with just the detector the arcade needs.
        if defaults.object(forKey: "detectPoses") == nil { Detector.store([.poses], in: defaults) }
        enabledDetectors = Detector.loadEnabled(from: defaults)
        rearCameraLens = CameraLens(rawValue: defaults.string(forKey: "epicwinRearLens") ?? "") ?? .wide
        keepScreenAwake = bool("epicwinKeepScreenAwake", default: true)''', "settings defaults")
    s = replace_once(s, 'useFrontCamera = bool("useFrontCamera", default: true)',
                     'useFrontCamera = bool("useFrontCamera", default: false)', "rear default")
    files["SettingsStore.swift"] = s

    s = files["AppModel.swift"]
    s = replace_once(s, "    private var processor: VisionProcessor?", '''    private(set) var cameraLensStatus = "Starting camera"
    private var isSceneActive = true
    private var hasStarted = false

    private var processor: VisionProcessor?''', "model state")
    s = replace_once(s, "    func start() {", '''    func start() {
        guard !hasStarted else { setSceneActive(true); return }
        hasStarted = true''', "start guard")
    s = replace_once(s, "        camera.start(position: settings.useFrontCamera ? .front : .back)",
                     "        configureCamera()", "start lens")
    s = replace_once(s, "    func stop() {\n        camera.stop()\n    }", '''    func stop() {
        isSceneActive = false
        UIApplication.shared.isIdleTimerDisabled = false
        camera.stop()
    }

    func setSceneActive(_ active: Bool) {
        isSceneActive = active
        UIApplication.shared.isIdleTimerDisabled = active && settings.keepScreenAwake
        if active && hasStarted { configureCamera() }
        else { camera.stop() }
    }

    private func configureCamera() {
        guard isSceneActive else { return }
        camera.start(position: settings.useFrontCamera ? .front : .back, lens: settings.rearCameraLens) { [weak self] status in
            Task { @MainActor [weak self] in self?.cameraLensStatus = status }
        }
    }''', "screen lifecycle")
    s = replace_once(s, "    func applySettings() {", '''    func applySettings() {
        UIApplication.shared.isIdleTimerDisabled = isSceneActive && settings.keepScreenAwake
        configureCamera()''', "apply lens and lock")
    s = replace_once(s, "        camera.switchCamera()", "        configureCamera()", "front switch")
    files["AppModel.swift"] = s

    s = files["Views/SettingsView.swift"]
    s = replace_once(s, '                Section("Camera") {', '''                Section("Camera") {
                    Picker("Rear lens", selection: $settings.rearCameraLens) {
                        ForEach(CameraLens.allCases) { lens in
                            Text(lens.label).tag(lens)
                        }
                    }
                    .pickerStyle(.segmented)
                    .disabled(settings.useFrontCamera)
                    LabeledContent("Active camera", value: model.cameraLensStatus)
                    if !CameraLens.ultraWideAvailable {
                        Text("This device has no rear 0.5x camera. Selecting it uses 1x instead.")
                            .font(.footnote)
                    }
                    Text("Rear lens only. Change the lens before calibration, not during a game.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    Toggle("Keep screen awake", isOn: $settings.keepScreenAwake)
                    Text("Prevents automatic locking while this app is in the foreground. Manual locking or switching apps can interrupt tracking.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)''', "settings camera UI")
    s = replace_once(s, "                .onChange(of: settings.cameraOrientation) {", '''                .onChange(of: settings.rearCameraLens) { model.applySettings() }
                .onChange(of: settings.keepScreenAwake) { model.applySettings() }
                .onChange(of: settings.cameraOrientation) {''', "settings observers")
    files["Views/SettingsView.swift"] = s

    s = files["Views/ControlBarView.swift"]
    s = replace_once(s, "    var body: some View {", "    var body: some View {\n        @Bindable var settings = model.settings", "quick picker binding")
    s = replace_once(s, "                Spacer()", '''                if !model.settings.useFrontCamera {
                    Picker("Rear lens", selection: $settings.rearCameraLens) {
                        ForEach(CameraLens.allCases) { lens in
                            Text(lens.label).tag(lens)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 140)
                    .background(.black.opacity(0.5), in: .capsule)
                    .onChange(of: model.settings.rearCameraLens) { model.applySettings() }
                    .accessibilityLabel("Rear camera lens")
                }

                Spacer()''', "quick lens picker")
    s = replace_once(s, "        .padding(.bottom, 8)", '''        .padding(.bottom, 8)
        .overlay(alignment: .top) {
            Text(model.cameraLensStatus)
                .font(.caption2)
                .foregroundStyle(.white)
                .padding(4)
                .background(.black.opacity(0.7), in: .capsule)
                .offset(y: -24)
                .allowsHitTesting(false)
        }''', "actual lens label")
    files["Views/ControlBarView.swift"] = s

    s = files["Views/ContentView.swift"]
    s = replace_once(s, "    @State private var model = AppModel()", r'''    @Environment(\.scenePhase) private var scenePhase
    @State private var model = AppModel()''', "scene lifecycle environment")
    s = replace_once(s, "        .sheet(isPresented: $showSettings) {", '''        .onChange(of: scenePhase) { model.setSceneActive(scenePhase == .active) }
        .onDisappear { model.stop() }
        .sheet(isPresented: $showSettings) {''', "scene lifecycle callbacks")
    files["Views/ContentView.swift"] = s
    return files


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(root):
    root = root.resolve()
    marker = root / "EPICWIN-PATCH.json"
    if marker.exists():
        raise ValueError("Already patched. Start with a fresh pinned upstream checkout.")
    files = patched_sources(root)
    # This is the multiplayer detector + mapping + wire encoder: never patched.
    protected = [root / "SenderCore" / p for p in
                 ("VisionProcessor.swift", "ObservationMapping.swift", "OSCSenderService.swift")]
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in protected}
    for name, content in files.items():
        (root / "Sender" / name).write_text(content, encoding="utf-8", newline="\n")
    for name in ("CameraManager.swift", "CameraLens.swift"):
        (root / "Sender" / name).write_bytes((KIT / "overrides" / name).read_bytes())
    # XcodeGen includes this .txt as an app resource; retain attribution in IPA too.
    (root / "Sender" / "TrackOSC-LICENSE.txt").write_bytes((KIT / "LICENSE-TrackOSC.txt").read_bytes())
    (root / "project-epicwin.yml").write_bytes((KIT / "project-epicwin.yml").read_bytes())
    metadata = {
        "upstream": "https://github.com/JGL/TrackOSC",
        "revision": (KIT / "UPSTREAM-REVISION.txt").read_text().strip(),
        "protected_sha256": hashes,
        "features": ["rear physical 0.5x / 1x selection", "foreground idle timer control"],
        "hardware_tested": False,
    }
    assert hashes == {p.relative_to(root).as_posix(): digest(p) for p in protected}
    marker.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print("EPICWIN_PATCH_OK - protocol/detector sources unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    apply(args.upstream)
