"""Offline tests for the vision→tap loop (no device, no adb)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shesh_phone.phone import Bounds  # noqa: E402
from shesh_phone.runner import Result  # noqa: E402
from shesh_phone.vision_loop import Target, TemplateVision, VisionTapLoop  # noqa: E402


class FakePhone:
    """Minimal Phone stand-in recording taps/screenshots."""

    def __init__(self, safe_area: Bounds | None = None) -> None:
        self.safe_area = safe_area or Bounds(0, 100, 1080, 2100)
        self.taps: list[tuple[int, int]] = []
        self.shots: list[str] = []
        self.shot_contents: dict[str, str] = {}
        self.fail_taps = False

    def screenshot(self, dest: str) -> bool:
        self.shots.append(dest)
        return True

    def tap(self, x: int, y: int) -> Result:
        if self.fail_taps:
            return Result("", "tap failed", 1)
        self.taps.append((x, y))
        return Result("", "", 0)


def test_loop_taps_when_target_found() -> None:
    phone = FakePhone()

    def vision(path: str, desc: str) -> Target | None:
        # target visible on the first shot, gone on the verify shot
        return Target(500, 1000, 0.95) if path == "/tmp/shesh-phone-1.png" else None

    loop = VisionTapLoop(phone, vision)
    ok, summary = loop.run("button")
    assert ok
    assert phone.taps == [(500, 1000)]
    assert "tapped (500,1000)" in summary


def test_loop_retries_when_target_not_found() -> None:
    phone = FakePhone()
    calls = []

    def vision(path: str, desc: str) -> Target | None:
        calls.append(path)
        return None  # never found

    loop = VisionTapLoop(phone, vision, max_attempts=3)
    ok, summary = loop.run("missing")
    assert not ok
    assert len(calls) == 3  # one screenshot per attempt
    assert phone.taps == []
    assert "not found" in summary


def test_loop_refuses_tap_outside_safe_area() -> None:
    phone = FakePhone()
    loop = VisionTapLoop(phone, lambda path, desc: Target(500, 50, 0.9))  # y=50 in status bar
    ok, summary = loop.run("status")
    assert not ok
    assert phone.taps == []
    assert "outside safe area" in summary


def test_loop_honest_failure_when_tap_errors() -> None:
    phone = FakePhone()
    phone.fail_taps = True
    loop = VisionTapLoop(phone, lambda path, desc: Target(500, 1000, 0.9))
    ok, summary = loop.run("button")
    assert not ok
    assert "tap failed" in summary


def test_loop_verifies_action_landed() -> None:
    """After a tap, the target should be gone on the verification screenshot."""
    phone = FakePhone()

    def vision(path: str, desc: str) -> Target | None:
        # first screenshot (attempt) + verify shot: target gone after tap
        if path == "/tmp/shesh-phone-1.png":
            return Target(500, 1000, 0.95)
        return None  # verify shot: target no longer present

    loop = VisionTapLoop(phone, vision)
    ok, summary = loop.run("button")
    assert ok
    assert phone.taps == [(500, 1000)]


def test_loop_gives_up_when_target_never_disappears() -> None:
    phone = FakePhone()

    def vision(path: str, desc: str) -> Target | None:
        return Target(500, 1000, 0.95)  # always present -> tap never lands

    loop = VisionTapLoop(phone, vision, max_attempts=2)
    ok, summary = loop.run("stubborn")
    assert not ok
    assert len(phone.taps) == 2
    assert "still present" in summary


def test_target_within_bounds() -> None:
    b = Bounds(0, 100, 1080, 2100)
    assert Target(500, 1000, 0.9).within(b)
    assert not Target(500, 50, 0.9).within(b)
    assert not Target(1200, 1000, 0.9).within(b)


def test_template_vision_finds_template(tmp_path) -> None:
    """Synthetic image test: the matcher finds a pasted template."""
    from PIL import Image, ImageDraw

    screen = Image.new("L", (200, 200), 255)
    templ = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(templ)
    draw.rectangle([2, 2, 17, 17], fill=128)
    screen.paste(templ, (120, 80))
    shot = tmp_path / "shot.png"
    tpath = tmp_path / "templ.png"
    screen.save(shot)
    templ.save(tpath)

    vision = TemplateVision(str(tpath), threshold=0.9)
    target = vision(str(shot), "marker")
    assert target is not None
    assert abs(target.x - (120 + 10)) <= 2
    assert abs(target.y - (80 + 10)) <= 2
    assert target.confidence >= 0.9


def test_template_vision_returns_none_when_absent(tmp_path) -> None:
    from PIL import Image

    screen = Image.new("L", (100, 100), 255)
    templ = Image.new("L", (10, 10), 0)
    shot = tmp_path / "shot.png"
    tpath = tmp_path / "templ.png"
    screen.save(shot)
    templ.save(tpath)

    vision = TemplateVision(str(tpath), threshold=0.9)
    assert vision(str(shot), "nothing") is None
