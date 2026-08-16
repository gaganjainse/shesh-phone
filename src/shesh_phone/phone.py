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


_STATUS_BAR_PX = 100
_NAV_BAR_PX = 100


class Phone:
    def __init__(self, serial: str | None = None,
                 runner: Callable[..., Result] = _run,
                 safe_area: Bounds | None = None) -> None:
        self.serial = serial
        self.runner = runner
        # Safe area prevents taps/swipes in status/nav bars.
        self._safe_area = safe_area
        self._safe_area_cache: Bounds | None = None

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

    @property
    def safe_area(self) -> Bounds:
        """Region of the screen that is safe to tap/swipe.

        Derived from the device's real resolution rather than assuming one
        model. An explicit safe_area passed to the constructor always wins.
        """
        if self._safe_area is not None:
            return self._safe_area
        if self._safe_area_cache is not None:
            return self._safe_area_cache
        size = self.screen_size()
        if size:
            w, h = size
            safe_h = max(0, h - _NAV_BAR_PX - _STATUS_BAR_PX)
            self._safe_area_cache = Bounds(0, _STATUS_BAR_PX, w, safe_h)
        else:
            # Device unreachable: refuse the whole screen rather than guess a
            # resolution and tap/swipe somewhere unintended.
            self._safe_area_cache = Bounds(0, 0, 0, 0)
        return self._safe_area_cache

    def screenshot(self, dest: str) -> bool:
        """Pull a PNG screenshot to dest.

        binary=True is required: the default runner decodes stdout with
        errors="replace", which corrupts every byte above 0x7F and yields an
        invalid PNG.
        """
        r = self.runner(self._adb("exec-out", "screencap", "-p"), binary=True)
        if not r.ok:
            return False
        data = r.stdout
        if isinstance(data, str):  # a runner that ignored binary=True
            return False
        Path(dest).write_bytes(data)
        return True

    # ── input ─────────────────────────────────────────────────────────
    def tap(self, x: int, y: int) -> Result:
        if not self.safe_area.contains(x, y):
            return Result("", f"refusing tap outside safe area: ({x},{y})", 1)
        return self.runner(self._adb("shell", "input", "tap", str(x), str(y)))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 300) -> Result:
        if not self.safe_area.contains(x1, y1) or not self.safe_area.contains(x2, y2):
            return Result(
                "",
                f"refusing swipe outside safe area: ({x1},{y1}) -> ({x2},{y2})",
                1,
            )
        if ms < 0:
            return Result("", "refusing swipe with negative duration", 1)
        return self.runner(self._adb(
            "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms)))

    def type_text(self, text: str) -> Result:
        # Escape spaces for adb shell input without invoking a local shell.
        return self.runner(self._adb("shell", "input", "text", text.replace(" ", "%s")))

    def press(self, key: str = "BACK") -> Result:
        return self.runner(self._adb("shell", "input", "keyevent", f"KEYCODE_{key.upper()}"))

    # ── apps ──────────────────────────────────────────────────────────
    def open_app(self, package: str) -> Result:
        return self.runner(self._adb("shell", "monkey", "-p", package, "-c",
                                     "android.intent.category.LAUNCHER", "1"))

    def current_focus(self) -> str:
        # Avoid relying on shell metacharacter parsing inside adb arguments.
        r = self.runner(self._adb(
            "shell", "sh", "-c", "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"))
        return r.stdout.strip()
