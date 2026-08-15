"""shesh-phone: ADB-based phone control (Realme Narzo target).

Inspired by the macOS phone-harness OCR/vision->tap loop, but built on Android
Debug Bridge. All adb calls go through an injectable runner so tests don't need
a device. Vision/OCR is a separate model call (the caller supplies it); this
module handles taps/swipes/input/screenshots/safe bounds.
"""
from __future__ import annotations

__version__ = "0.1.0"
