# cr-agent

Phone-only experiment: an agent harness that plays Clash Royale (Training Camp only) on a
single Android phone, inspired by *PlayScriptBench* (arXiv 2611.27741) — the LLM writes and
tunes fast game-playing code instead of looking at every frame.

Everything runs on the phone: the game as a normal app, and Termux (no proot) running adb over
Wireless debugging to the phone itself, Python, and later Claude Code.

## Layout

| Path | What |
|---|---|
| `bridge/SETUP.md` | Step-by-step setup: phone settings, Termux packages, venv, adb pairing, start test |
| `bridge/bridge.py` | The only path from code to the phone: screenshot / tap / swipe; taps refused unless Clash Royale is in front |
| `bridge/bridge_test.py` | Start test: device info, screenshot latency, stream fps, optional tap |
| `knowledge/clash_royale_player_knowledge.md` | What a player needs to know, mapped to agent state and skills |
| `.claude/settings.json` | Claude Code permissions for this project (no raw adb, pkg, rm -rf, sdcard) |

## Quick start (Termux)

```bash
pkg install git android-tools python python-numpy opencv-python python-pillow
git clone https://github.com/Jivraj-18/cr-agent && cd cr-agent
python -m venv --system-site-packages .venv && . .venv/bin/activate
pip install adbutils
# pair adb with the phone itself — see bridge/SETUP.md
cd bridge && python bridge_test.py --stream 5
```

## Notes

- Use a spare game account and Training Camp; automation is against Supercell's terms.
- Not affiliated with or endorsed by Supercell.
