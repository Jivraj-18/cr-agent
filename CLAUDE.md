# cr-agent — instructions for Claude Code (running on the phone)

## What this is
An experiment: an agent harness that plays Clash Royale on this same Android phone (Moto G96),
inspired by PlayScriptBench (arXiv 2611.27741). Claude writes and tunes fast Python code that
plays; Claude itself is the slow loop (between matches / on big events), not a per-frame player.

## Environment
- You are running in **native Termux** (no proot) on the phone that also runs the game.
- adb talks to the phone itself over Wireless debugging. The adb server runs in Termux on
  127.0.0.1:5037. The device shows up as `<wifi-ip>:<port>` (e.g. `10.67.98.177:45435`).
- Python venv: `~/cr-agent/.venv` (created with `--system-site-packages`; numpy/OpenCV/Pillow
  come from Termux `pkg`). Run Python as `.venv/bin/python` from the repo root, or
  `../.venv/bin/python` from `bridge/`.

## Hard rules
1. **All phone interaction goes through `bridge/bridge.py`** (screenshot / tap / swipe /
   foreground check). Never call `adb shell input`, `adb install`, `pm`, `settings`, or other
   adb shell commands directly. The only raw adb you may run: `adb devices`, `adb connect`.
2. Taps only while Clash Royale (`com.supercell.clashroyale`) is in front — bridge.py enforces it;
   don't work around it.
3. **Training Camp only** (battles vs the game's AI). Never start ladder/ranked or play against
   real people. Never spend gems/gold, buy anything, or change account settings.
4. Don't run `termux-setup-storage`, don't read `/sdcard` or `/storage`, don't touch other apps.
5. If adb isn't connected, don't try to fix pairing yourself — ask the user for the current
   port from Settings → Developer options → Wireless debugging → "IP address and port", then
   run `adb connect <ip>:<port>`.
6. Keep changes inside this repo. Commit with clear messages when something works.

## Files
- `bridge/SETUP.md` — how the phone was set up
- `bridge/bridge.py` — gated phone control layer
- `bridge/bridge_test.py` — start test (writes `bridge/out/report.json`, `bridge/out/frame.png`)
- `knowledge/clash_royale_player_knowledge.md` — game rules and what the agent must track

## Current task: bridge start test (SETUP.md step 5)
1. `adb devices` — confirm one device is listed as `device`. If not, see rule 5.
2. Ask the user to open Clash Royale and start a **Training Camp** match, and to say when it's running.
3. From `bridge/`: `../.venv/bin/python bridge_test.py` (read-only), then try
   `../.venv/bin/python bridge_test.py --stream 5` (needs PyAV; if `pip install av` would
   compile from source for a long time, skip the stream test and say so).
4. Read `out/report.json`, look at `out/frame.png`, and report to the user:
   screen size, whether Clash Royale was detected in front, screenshot latencies
   (png vs raw), stream fps if measured, and what you can see in the frame
   (elixir bar, hand cards, towers). Compare against the thresholds in SETUP.md.
5. Don't tap yet. Next task (after the user agrees) is calibrating screen regions for
   elixir, hand and towers from real frames.
