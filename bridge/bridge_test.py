#!/usr/bin/env python3
"""
Bridge start test — everything goes through bridge.Bridge (the gated layer).

  python bridge_test.py                 device info, foreground app, screenshot timing
  python bridge_test.py --stream 5      + 5 s H.264 stream fps (needs PyAV: `pip install av`)
  python bridge_test.py --tap X Y       + one tap (refused unless Clash Royale is in front)

Writes out/frame.png and out/report.json.
"""
import argparse
import json
import os
import statistics
import time

from bridge import Bridge, BridgeError

OUT = "out"


def timed(fn, n=5):
    ts, last = [], None
    for _ in range(n):
        t0 = time.perf_counter()
        last = fn()
        ts.append(round((time.perf_counter() - t0) * 1000, 1))
    return {"median_ms": statistics.median(ts), "min_ms": min(ts), "max_ms": max(ts)}, last


def stream_test(b, seconds):
    try:
        import av
    except ImportError:
        return {"error": "PyAV not installed (pip install av) — skipping stream test"}
    conn = b.screen_stream(int(seconds) + 2)
    sock = conn.conn
    sock.settimeout(3)
    codec = av.CodecContext.create("h264", "r")
    frames, first, t0 = 0, None, time.perf_counter()
    try:
        while time.perf_counter() - t0 < seconds:
            chunk = sock.recv(65536)
            if not chunk:
                break
            for pkt in codec.parse(chunk):
                for _ in codec.decode(pkt):
                    frames += 1
                    if first is None:
                        first = round((time.perf_counter() - t0) * 1000, 1)
    except Exception as e:
        return {"error": repr(e), "frames": frames}
    finally:
        conn.close()
    dur = time.perf_counter() - t0
    # screenrecord only emits frames when the screen changes: run during a live match.
    return {"frames": frames, "seconds": round(dur, 2),
            "stream_fps": round(frames / dur, 1), "first_frame_ms": first}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", type=float, default=0)
    ap.add_argument("--tap", nargs=2, type=int, metavar=("X", "Y"))
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    b = Bridge()
    d = b._d
    report = {
        "device": {
            "model": d.shell("getprop ro.product.model").strip(),
            "android": d.shell("getprop ro.build.version.release").strip(),
            "screen": f"{b.width}x{b.height}",
        },
        "foreground": b.foreground_activity(),
        "clash_royale_in_front": b.clash_royale_in_front(use_cache=False),
    }
    print(json.dumps(report, indent=2))

    report["screencap_png"], png = timed(b.screenshot_png)
    with open(f"{OUT}/frame.png", "wb") as f:
        f.write(png)
    report["screencap_raw"], frame = timed(b.screenshot)
    report["frame_shape"] = list(frame.shape)
    print("screencap_png:", report["screencap_png"])
    print("screencap_raw:", report["screencap_raw"], frame.shape)

    if a.stream:
        report["stream"] = stream_test(b, a.stream)
        print("stream:", report["stream"])

    if a.tap:
        t0 = time.perf_counter()
        try:
            b.tap(*a.tap)
            report["tap_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        except BridgeError as e:
            report["tap_error"] = str(e)
        print("tap:", report.get("tap_ms", report.get("tap_error")))

    with open(f"{OUT}/report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nwrote {OUT}/frame.png and {OUT}/report.json")


if __name__ == "__main__":
    main()
