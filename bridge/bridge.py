"""
bridge.py — the ONLY way agent code touches the phone.

Exposes a tiny surface: screenshot / tap / swipe / foreground check.
Taps and swipes are refused unless Clash Royale is the app in front and the
coordinates are on screen. Nothing else (install, settings, shell) is exposed.
"""
import time

import adbutils
import numpy as np

CR_PACKAGE = "com.supercell.clashroyale"


class BridgeError(RuntimeError):
    pass


class Bridge:
    def __init__(self, host="127.0.0.1", port=5037, fg_cache_s=1.0):
        devices = adbutils.AdbClient(host=host, port=port).device_list()
        if not devices:
            raise BridgeError(
                "No device on adb. In Termux: adb connect localhost:<port>; adb devices"
            )
        self._d = devices[0]
        size = self._d.shell("wm size").strip().splitlines()[-1].split(":")[-1].strip()
        self.width, self.height = (int(v) for v in size.split("x"))
        self._fg_cache_s = fg_cache_s
        self._fg_t = 0.0
        self._fg_ok = False

    # ---------- read-only ----------
    def foreground_activity(self) -> str:
        out = self._d.shell(
            "dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity'"
        )
        return out.strip().splitlines()[0].strip() if out.strip() else ""

    def clash_royale_in_front(self, use_cache=True) -> bool:
        now = time.monotonic()
        if use_cache and now - self._fg_t < self._fg_cache_s:
            return self._fg_ok
        self._fg_ok = CR_PACKAGE in self.foreground_activity()
        self._fg_t = now
        return self._fg_ok

    def screenshot(self) -> np.ndarray:
        """Raw screencap → HxWx3 RGB uint8 (no PNG encoding on the phone)."""
        data = self._d.shell("screencap", encoding=None)
        w = int.from_bytes(data[0:4], "little")
        h = int.from_bytes(data[4:8], "little")
        header = len(data) - w * h * 4
        return np.frombuffer(data[header:], dtype=np.uint8).reshape(h, w, 4)[:, :, :3]

    def screenshot_png(self) -> bytes:
        return self._d.shell("screencap -p", encoding=None)

    def screen_stream(self, seconds: int, size="720x1600", bitrate=4_000_000):
        """H.264 stream socket from screenrecord (read-only). Caller decodes."""
        return self._d.shell(
            f"screenrecord --output-format=h264 --size {size} "
            f"--bit-rate {bitrate} --time-limit {int(seconds)} -",
            stream=True,
        )

    # ---------- gated input ----------
    def _guard(self, *points):
        if not self.clash_royale_in_front():
            raise BridgeError("Refused: Clash Royale is not the app in front.")
        for x, y in points:
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise BridgeError(f"Refused: ({x},{y}) is off screen {self.width}x{self.height}.")

    def tap(self, x: int, y: int):
        x, y = int(x), int(y)
        self._guard((x, y))
        self._d.shell(f"input tap {x} {y}")

    def swipe(self, x1, y1, x2, y2, ms=150):
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        self._guard((x1, y1), (x2, y2))
        self._d.shell(f"input swipe {x1} {y1} {x2} {y2} {int(ms)}")
