# Setup — phone only (Moto G96), Termux, no proot

```
 Android                                   Termux  (~/cr-agent, own venv)
┌────────────────────┐   wireless       ┌───────────────────────────────────────┐
│ Clash Royale app   │◄── debugging ───►│ adb server (android-tools)            │
│ adbd               │   (localhost)    │ bridge.py  ← the only path to phone   │
└────────────────────┘                  │   screenshot / tap / swipe            │
                                        │   taps refused unless CR is in front  │
                                        │ bridge_test.py, later the agent       │
                                        │ Claude Code (.claude/settings.json    │
                                        │   denies raw adb, pkg, rm -rf, sdcard)│
                                        └───────────────────────────────────────┘
```

## 0. Clash Royale

1. Install Clash Royale from the Play Store.
2. Use a **spare account**, not your main one (bots break Supercell's terms; a ban hits that
   account). If the game auto-loads your main account via Google Play Games / Supercell ID,
   log out in game settings and start a fresh account.
3. Finish the in-game tutorial. Use **Training Camp** (vs the game's AI) for every test.

## 1. Phone settings

1. Settings → About phone → tap **Build number** 7× → Developer options.
2. Developer options → **Wireless debugging** ON (phone must be on Wi-Fi).
3. Optional: Developer options → **Pointer location** ON while we calibrate taps.
4. Do **not** grant Termux storage access (`termux-setup-storage`) — keeps photos/downloads
   out of reach of the experiment.

## 2. Termux packages

```bash
pkg update && pkg upgrade
pkg install android-tools python python-numpy opencv-python python-pillow
termux-wake-lock
```

(If a name isn't found: `pkg search opencv`, `pkg search numpy`.)

## 3. Get the project onto the phone

```bash
pkg install git
cd ~ && git clone https://github.com/Jivraj-18/cr-agent
cd ~/cr-agent
python -m venv --system-site-packages .venv   # sees pkg's numpy/OpenCV, isolates pip installs
. .venv/bin/activate
pip install adbutils
pip install av        # optional, for the stream test; skip if it tries to compile for long
```

To remove the whole experiment later: `rm -rf ~/cr-agent`.

## 4. Pair adb with the phone itself

Split-screen: Settings (top), Termux (bottom). Wireless debugging → **Pair device with
pairing code**:

```bash
adb pair localhost:<PAIR_PORT> <CODE>
adb connect localhost:<CONNECT_PORT>     # the main "IP address & Port" port
adb devices                              # expect: localhost:<port>   device
```

After reboot / toggling Wireless debugging: only `adb connect` with the new port.
**Turn Wireless debugging OFF when you're done experimenting.**

## 5. Start test

Start a Training Camp match, then quickly in Termux (split-screen helps):

```bash
cd ~/cr-agent/bridge && . ../.venv/bin/activate
python bridge_test.py --stream 5
```

Send me `out/report.json` and `out/frame.png`. To get them out without storage permission:
`termux-open out/frame.png` (opens the Android share sheet) — or just paste report.json text.

| Metric | Good enough | Why |
|---|---|---|
| `screencap_raw` median | < 300 ms | fallback perception path |
| `stream.stream_fps` | ≥ 5 | fast-loop perception |
| `tap_ms` (with `--tap X Y`) | < 150 ms | decision → finger-down |

## 6. Claude Code (not needed for the start test)

Current Claude Code is a glibc binary and Termux uses Bionic libc, so plain `npm install`
fails. Use the native-Termux glibc-runner route (e.g. github.com/ferrumclaudepilgrim/
claude-code-android, "Path A") — read the script before running it. Run `claude` from inside
`~/cr-agent` so `.claude/settings.json` applies.
