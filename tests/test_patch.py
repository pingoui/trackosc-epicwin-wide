import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

KIT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("epicwin_patch", KIT / "apply_patch.py")
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


def copy_pinned_sources(root):
    # Read the pinned git objects, not a worktree that may already have the overlay.
    # This makes tests repeatable before AND after manually applying the patch.
    upstream = KIT / "upstream"
    revision = (KIT / "UPSTREAM-REVISION.txt").read_text().strip()
    result = subprocess.run(["git", "-C", str(upstream), "archive", "--format=zip",
                             revision, "Sender", "SenderCore"], check=True, capture_output=True)
    with zipfile.ZipFile(io.BytesIO(result.stdout)) as archive:
        for entry in archive.infolist():
            target = (root / entry.filename).resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError("Unsafe fixture path")
        archive.extractall(root)


class PatchTests(unittest.TestCase):
    def test_anchor_refuses_missing_or_duplicate(self):
        for source in ("nothing", "anchor anchor"):
            with self.assertRaises(ValueError):
                patch.replace_once(source, "anchor", "replacement", "test")

    def test_physical_lens_and_fallback(self):
        camera = (KIT / "overrides/CameraManager.swift").read_text(encoding="utf-8")
        lens = (KIT / "overrides/CameraLens.swift").read_text(encoding="utf-8")
        self.assertIn("builtInUltraWideCamera", lens)
        self.assertIn("newPosition == .back ? lens.deviceType : .builtInWideAngleCamera", camera)
        self.assertIn('0.5x unavailable - using rear 1x', camera)
        self.assertNotIn("videoZoomFactor", camera)  # not a digital zoom workaround
        self.assertIn("alwaysDiscardsLateVideoFrames = true", camera)
        self.assertIn("isVideoMirrored = false", camera)
        self.assertIn("previous camera retained", camera)

    def test_separate_identity(self):
        project = (KIT / "project-epicwin.yml").read_text(encoding="utf-8")
        self.assertIn("pl.epicwin.trackosc.wide", project)
        self.assertIn("TrackOSC EpicWin", project)
        self.assertIn("exactVersion: 3.1.0", project)

    def test_pinned_source_application_and_protocol_unchanged(self):
        upstream = KIT / "upstream"
        self.assertTrue((upstream / "Sender/AppModel.swift").exists(),
                        "First checkout the pinned upstream into kit/upstream; see README")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_pinned_sources(root)
            protected = [root / "SenderCore" / name for name in
                         ("VisionProcessor.swift", "ObservationMapping.swift", "OSCSenderService.swift")]
            before = [p.read_bytes() for p in protected]
            patch.apply(root)
            self.assertEqual(before, [p.read_bytes() for p in protected])
            self.assertTrue((root / "Sender/CameraLens.swift").exists())
            self.assertIn("Joel Gethin Lewis", (root / "Sender/TrackOSC-LICENSE.txt").read_text())
            settings = (root / "Sender/SettingsStore.swift").read_text()
            self.assertIn('default: false)', settings)
            self.assertIn('Detector.store([.poses], in: defaults)', settings)
            self.assertIn('rearCameraLens = CameraLens(rawValue:', settings)
            model = (root / "Sender/AppModel.swift").read_text()
            self.assertIn("active && settings.keepScreenAwake", model)
            self.assertIn("UIApplication.shared.isIdleTimerDisabled = false", model)
            self.assertNotIn("camera.switchCamera()", model)
            ui = (root / "Sender/Views/SettingsView.swift").read_text()
            self.assertIn(".disabled(settings.useFrontCamera)", ui)
            self.assertIn("model.cameraLensStatus", ui)
            self.assertIn(".onChange(of: settings.rearCameraLens)", ui)
            content = (root / "Sender/Views/ContentView.swift").read_text()
            self.assertIn("scenePhase == .active", content)
            with self.assertRaises(ValueError):
                patch.apply(root)

    def test_unknown_source_is_not_partially_patched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_pinned_sources(root)
            changed = root / "Sender/Views/ContentView.swift"
            changed.write_text(changed.read_text(encoding="utf-8").replace(
                "@State private var model = AppModel()", "@State private var renamed = AppModel()"), encoding="utf-8")
            before = {p.relative_to(root): p.read_bytes() for p in (root / "Sender").rglob("*.swift")}
            with self.assertRaises(ValueError):
                patch.apply(root)
            after = {p.relative_to(root): p.read_bytes() for p in (root / "Sender").rglob("*.swift")}
            self.assertEqual(before, after)
            self.assertFalse((root / "EPICWIN-PATCH.json").exists())


if __name__ == "__main__":
    unittest.main()
