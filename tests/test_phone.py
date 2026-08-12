"""Offline tests for shesh-phone (no device/adb needed)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shesh_phone.phone import Bounds, Phone  # noqa: E402
from shesh_phone.runner import Result  # noqa: E402


def fake_runner(stdout="", returncode=0, binary=False):
    calls = []

    def _run(cmd, **kw):
        calls.append(cmd)
        out = stdout.encode() if binary else stdout
        return Result(out, "", returncode)

    _run.calls = calls
    return _run


def test_is_connected():
    p = Phone(runner=fake_runner("device\n"))
    assert p.is_connected()
    p2 = Phone(runner=fake_runner("", returncode=1))
    assert not p2.is_connected()


def test_screen_size_parsing():
    p = Phone(runner=fake_runner("Physical size: 1080x2400\n"))
    assert p.screen_size() == (1080, 2400)


def test_tap_inside_safe_area():
    r = fake_runner()
    p = Phone(runner=r, safe_area=Bounds(0, 100, 1080, 2100))
    res = p.tap(500, 1000)
    assert res.ok
    assert any("input" in c and "tap" in c for c in r.calls)


def test_tap_refused_outside_safe_area():
    p = Phone(runner=fake_runner(), safe_area=Bounds(0, 100, 1080, 2100))
    res = p.tap(10, 10)  # status bar
    assert not res.ok


def test_swipe_and_type():
    r = fake_runner()
    p = Phone(runner=r)
    p.swipe(100, 500, 100, 1000)
    p.type_text("hello world")
    joined = " ".join(" ".join(c) for c in r.calls)
    assert "swipe" in joined
    assert "%s" in joined  # spaces escaped


def test_serial_passed_to_adb():
    r = fake_runner()
    Phone(serial="emulator-5554", runner=r).press("HOME")
    assert "-s" in r.calls[0] and "emulator-5554" in r.calls[0]


def test_screenshot_writes_bytes(tmp_path):
    r = fake_runner(stdout="PNGDATA", binary=True)
    dest = tmp_path / "shot.png"
    p = Phone(runner=r)
    assert p.screenshot(str(dest))
    assert dest.read_bytes() == b"PNGDATA"
