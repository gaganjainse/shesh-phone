# 📱 shesha-phone

**ADB control for an Android phone** (target: Realme Narzo on CachyOS).
Safe-bounds tapping, swipes, text input, screenshots, and app launching — with
all `adb` calls injectable so it's fully testable offline.

- License: GPL-3.0
- Layer: Soma
- Part of: [Shesha ecosystem](https://github.com/gaganjainse/shesha-ecosystem)

## Design

- A safe area (default `Bounds(0,100,1080,2100)`) refuses taps into the status/nav bars.
- Vision/OCR is **not** here — the caller supplies an image model and calls `tap()`.
- No secrets; adb serial is configurable per-device.

## Develop

```bash
uv sync --extra dev
uv run pytest -q        # 7 offline tests (adb is faked)
uv run ruff check .
```
