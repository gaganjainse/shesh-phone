"""Thin, safe wrapper around `adb` for one device."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .runner import Result
from .runner import run as _run


@dataclass
class Bounds:
    x: int
    y: int
    w: int
    h: int

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h


class Phone:
    def __init__(self, serial: str | None = None,
                 runner: Callable[..., Result] = _run,
                 safe_area: Bounds | None = None) -> None:
        self.serial = serial
        self.runner = runner
        # Safe area prevents taps in status/nav bars.
        self.safe_area = safe_area or Bounds(0, 100, 1080, 2100)

    def _adb(self, *args: str) -> list[str]:
        cmd = ["adb"]
        if self.serial:
            cmd += ["-s", self.serial]
        cmd += list(args)
        return cmd

    # ── device ────────────────────────────────────────────────────────
    def is_connected(self) -> bool:
        r = self.runner(self._adb("get-state"))
        return r.ok and "device" in r.stdout

    def screen_size(self) -> tuple[int, int] | None:
        r = self.runner(self._adb("shell", "wm", "size"))
        if not r.ok:
            return None
        # "Physical size: 1080x2400"
        for part in r.stdout.split():
            if "x" in part and part.replace("x", "").isdigit():
                w, h = part.split("x")
                return int(w), int(h)
        return None

    def screenshot(self, dest: str) -> bool:
        # adb exec-out screencap avoids a temp file on device.
        r = self.runner(self._adb("exec-out", "screencap", "-p"))
        if not r.ok:
            return False
        Path(dest).write_bytes(r.stdout.encode("latin-1") if isinstance(r.stdout, str) else r.stdout)
        return True

    # ── input ─────────────────────────────────────────────────────────
    def tap(self, x: int, y: int) -> Result:
        if not self.safe_area.contains(x, y):
            return Result("", f"refusing tap outside safe area: ({x},{y})", 1)
        return self.runner(self._adb("shell", "input", "tap", str(x), str(y)))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 300) -> Result:
        return self.runner(self._adb(
            "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms)))

    def type_text(self, text: str) -> Result:
        # Escape spaces for adb shell input.
        return self.runner(self._adb("shell", "input", "text", text.replace(" ", "%s")))

    def press(self, key: str = "BACK") -> Result:
        return self.runner(self._adb("shell", "input", "keyevent", f"KEYCODE_{key.upper()}"))

    # ── apps ──────────────────────────────────────────────────────────
    def open_app(self, package: str) -> Result:
        return self.runner(self._adb("shell", "monkey", "-p", package, "-c",
                                     "android.intent.category.LAUNCHER", "1"))

    def current_focus(self) -> str:
        r = self.runner(self._adb("shell", "dumpsys", "window", "|", "grep", "-E", "mCurrentFocus"))
        return r.stdout.strip()
