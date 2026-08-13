"""Real hot-path benchmarks for shesh-phone (stdlib only, CI-safe).

Measures the vision→tap loop cycle and template matching on a synthetic
screen — the latency-critical path for voice-driven device control.
Median of N runs, loose bounds. Run:  python benchmarks/bench_hotpaths.py
"""

from __future__ import annotations

import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shesh_phone.phone import Bounds, Phone  # noqa: E402
from shesh_phone.runner import Result  # noqa: E402
from shesh_phone.vision_loop import Target, TemplateVision, VisionTapLoop  # noqa: E402


def bench(label: str, fn, n: int = 200) -> float:
    times: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    med = statistics.median(times)
    print(f"  {label:44s} median {med * 1e6:9.2f} µs  (n={n})")
    return med


class _FakePhone:
    def __init__(self) -> None:
        self.safe_area = Bounds(0, 100, 1080, 2100)

    def screenshot(self, dest: str) -> bool:
        return True

    def tap(self, x: int, y: int) -> Result:
        return Result("", "", 0)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="shesh-phone-bench-"))

    # Vision→tap loop: find button on first shot, gone on verify shot.
    phone = _FakePhone()

    def vision(path: str, desc: str) -> Target | None:
        if path == "/tmp/shesh-phone-1.png":
            return Target(500, 1000, 0.95)
        return None

    loop = VisionTapLoop(phone, vision)
    bench("vision→tap cycle (find+tap+verify)", lambda: loop.run("button"), n=100)

    # Template match on a synthetic 400x800 screen with a 40x40 marker.
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  (pillow not installed — template bench skipped)")
        return 0

    screen = Image.new("L", (400, 800), 255)
    templ = Image.new("L", (40, 40), 0)
    ImageDraw.Draw(templ).rectangle([4, 4, 35, 35], fill=128)
    screen.paste(templ, (200, 400))
    shot = tmp / "screen.png"
    tpath = tmp / "marker.png"
    screen.save(shot)
    templ.save(tpath)
    vision = TemplateVision(str(tpath), threshold=0.9)
    bench("template match (400x800 screen)", lambda: vision(str(shot), "marker"), n=50)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
