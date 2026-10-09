# TrackOSC EpicWin — selectable rear 0.5x / 1x camera

Start with [00-START-TUTAJ.md](00-START-TUTAJ.md) (Polish instructions for Windows).

This is a small build kit, not a prebuilt or signed iPhone application. GitHub Actions
checks out TrackOSC commit `f4a241ad59faf851927081280753f1855ff3c112`, tests and applies
the camera/UI overlay, generates an iOS-only Xcode project, and builds a physical-device
Release IPA without Apple signing credentials. Sign/install the artifact locally using
AltStore Classic. The build has a separate bundle identifier and display name.

Changes:

- Rear physical lens selector, 1x and 0.5x, saved in UserDefaults.
- Quick segmented selector in the live view and a selector in Settings.
- Actual camera status; unavailable ultra-wide falls back to 1x explicitly.
- Front camera switch preserved, rear lens remembered while using front camera.
- Failed camera switches retain the previous input where possible.
- Foreground idle-timer prevention (enabled by default, configurable).
- Camera stops when the app becomes inactive and resumes when active again.
- First launch defaults to rear 1x and only 2D Body enabled.
- Apple Vision detection, joint mapping, OSC sender and unmirrored coordinates unchanged.

No Unity changes, no alteration of the existing Camo input, no claim of measured latency,
multi-person accuracy, thermal endurance or successful installation on a physical iPhone.
Switch lenses before game calibration. Ultra-wide framing can reduce the pixels per person.

## Reproduce local source tests

Run from the kit directory. Python 3.11+ and Git are needed; no Xcode needed for these tests.

```powershell
git clone --filter=blob:none https://github.com/JGL/TrackOSC.git upstream
git -C upstream checkout --detach f4a241ad59faf851927081280753f1855ff3c112
python -m unittest discover -s tests -v
python apply_patch.py upstream
```

The patch refuses unexpected anchors and already patched directories. Tests use temporary
copies, verify that detection/mapping/OSC sources remain byte-identical, and check UI,
defaults, lifecycle wiring and fallback code. These are structural tests, not Swift type
checking or camera hardware tests. GitHub Actions is the required Swift compilation check.

For a Mac with Xcode installed, after applying the patch:

```sh
cd upstream
brew install xcodegen
xcodegen generate --spec project-epicwin.yml
open TrackOSCEpicWin.xcodeproj
```

Select your own signing team before installing from Xcode. The original project is not
rewritten. The app's minimum deployment target is inherited as iOS 18. The actual cloud
build is still required to confirm Swift/SDK compatibility; it has not run in this workspace.

## Recover from interrupted publishing

`Prepare-GitHub.ps1` never overwrites an existing `github-upload` directory. If preparation
succeeded but authentication or publishing failed, use GitHub Desktop to publish that
folder, or from a terminal in that folder:

```powershell
gh auth login
gh repo create trackosc-epicwin-wide --public --source . --remote origin --push
```

If the remote repository was already created, inspect `git remote -v` and `gh repo view`
before retrying; do not create another repository or force-push blindly.

## License / attribution

TrackOSC is by Joel Gethin Lewis, MIT license, preserved in `LICENSE-TrackOSC.txt` and in
the downloadable artifact. This is an unofficial EpicWin modification, not an upstream
release. The dependency is downloaded from its public source only when the build runs.
The exact source revision and SHA-256 of untouched protocol sources are included in
`EPICWIN-PATCH.json`; `SHA256.txt` identifies the generated unsigned IPA.
