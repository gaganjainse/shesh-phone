"""Regressions for defects found in the 2026-08-15 fleet audit."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shesh_phone.phone import Bounds, Phone  # noqa: E402
from shesh_phone.runner import Result  # noqa: E402

# A one-pixel PNG. Every byte above 0x7F here is what the old code destroyed.
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


# ── BUG-4: screenshots were decoded to str and re-encoded, corrupting them ──

def test_screenshot_requests_binary_output():
    """The runner must be called with binary=True.

    Without it the runner decodes stdout with errors="replace", turning every
    byte above 0x7F into U+FFFD. Re-encoding as latin-1 cannot recover them,
    so the written file is not a valid PNG.
    """
    seen = {}

    def runner(cmd, **kw):
        seen.update(kw)
        return Result(PNG, "", 0)

    p = Phone(runner=runner, safe_area=Bounds(0, 0, 1080, 2400))
    p.screenshot("/tmp/shot.png")
    assert seen.get("binary") is True, "screenshot must request binary output"


def test_screenshot_writes_bytes_unchanged(tmp_path):
    dest = tmp_path / "shot.png"

    def runner(cmd, **kw):
        return Result(PNG, "", 0)

    p = Phone(runner=runner, safe_area=Bounds(0, 0, 1080, 2400))
    assert p.screenshot(str(dest)) is True
    written = dest.read_bytes()
    assert written == PNG, "screenshot bytes were altered in transit"
    assert written.startswith(b"\x89PNG"), "not a valid PNG header"


def test_screenshot_refuses_a_decoded_stream(tmp_path):
    """If a runner ignores binary=True, fail rather than write a corrupt file."""
    def bad_runner(cmd, **kw):
        return Result(PNG.decode("latin-1"), "", 0)

    p = Phone(runner=bad_runner, safe_area=Bounds(0, 0, 1080, 2400))
    assert p.screenshot(str(tmp_path / "x.png")) is False


# ── ARCH-1: the safe area hardcoded one device's resolution ─────────────────

def test_safe_area_derives_from_the_real_screen_size():
    """The default was Bounds(0, 100, 1080, 2100), a guess for one phone.

    On a 1080x2400 device that leaves 300px unreachable; on any other
    resolution the bounds are simply wrong.
    """
    def runner(cmd, **kw):
        return Result("Physical size: 1440x3200", "", 0)

    p = Phone(runner=runner)
    area = p.safe_area
    assert area.w == 1440, "width must follow the device"
    assert area.y == 100 and area.h == 3100, "bars excluded from the real height"


def test_safe_area_covers_the_full_width_of_a_tall_device():
    def runner(cmd, **kw):
        return Result("Physical size: 1080x2400", "", 0)

    p = Phone(runner=runner)
    assert p.safe_area.contains(540, 2250), "lower screen wrongly unreachable"


def test_explicit_safe_area_wins():
    def runner(cmd, **kw):
        return Result("Physical size: 1440x3200", "", 0)

    explicit = Bounds(10, 20, 30, 40)
    assert Phone(runner=runner, safe_area=explicit).safe_area == explicit


def test_safe_area_refuses_everything_when_the_device_is_unreachable():
    """Better to refuse than to guess a resolution and tap blind."""
    def runner(cmd, **kw):
        return Result("", "device not found", 1)

    p = Phone(runner=runner)
    assert p.safe_area == Bounds(0, 0, 0, 0)
    assert not p.safe_area.contains(500, 500)


def test_safe_area_is_queried_once():
    calls = []

    def runner(cmd, **kw):
        calls.append(cmd)
        return Result("Physical size: 1080x2400", "", 0)

    p = Phone(runner=runner)
    seen = [p.safe_area, p.safe_area, p.safe_area]
    assert len(set(map(id, seen))) == 1, "the cached object should be reused"
    assert len(calls) == 1, "screen size should be queried once"
