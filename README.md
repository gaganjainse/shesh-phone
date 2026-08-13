# 📱 shesh-phone

**ADB control for an Android phone** (target: Realme Narzo on CachyOS).
Safe-bounds tapping, swipes, text input, screenshots, and app launching — with
all `adb` calls injectable so it's fully testable offline.

- License: GPL-3.0
- Layer: Soma
- Part of: [Shesh ecosystem](https://github.com/gaganjainse/shesh-ecosystem)

## Design

- A safe area (default `Bounds(0,100,1080,2100)`) refuses taps into the status/nav bars.
- Vision/OCR: `shesh_phone.vision_loop.VisionTapLoop` implements the
  screenshot → locate → tap → verify loop (retries honestly, refuses taps
  outside the safe area). The vision provider is injected: use the built-in
  `TemplateVision` (PIL template matcher, offline) or any model callable.
  9 tests cover the loop + matcher.
- No secrets; adb serial is configurable per-device.

## Develop

```bash
uv sync --extra dev
uv run pytest -q        # 7 offline tests (adb is faked)
uv run ruff check .
```

## Security

Security posture and vulnerability reporting: [canonical ecosystem security
policy](https://github.com/gaganjainse/shesh-ecosystem/blob/main/SECURITY.md).
