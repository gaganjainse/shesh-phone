# 📱 shesh-phone

> **ADB control for an Android phone** (target: Realme Narzo on CachyOS). Safe-bounds
> tapping, swipes, text input, screenshots, and app launching — with all `adb`
> calls injectable so it's fully testable offline.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python) ![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue?style=for-the-badge) ![Tests](https://img.shields.io/badge/Tests-16-success?style=for-the-badge) ![CI](https://img.shields.io/github/actions/workflow/status/gaganjainse/shesh-phone/ci.yml?style=for-the-badge&label=CI)

- **License:** GPL-3.0-or-later
- **Owner:** Gagan Jain ([@gaganjainse](https://github.com/gaganjainse))
- **Layer:** Soma (sensors & actuators)
- **Part of:** [shesh-ecosystem](https://github.com/gaganjainse/shesh-ecosystem)

---

## Quick start

```bash
uv sync --extra dev
uv run pytest -q        # 16 offline tests (adb is faked)
uv run ruff check .
```

## Design

- A **safe area** (default `Bounds(0,100,1080,2100)`) refuses taps into the
  status/nav bars.
- **Vision/OCR:** `VisionTapLoop` runs the screenshot → locate → tap → verify loop,
  retries honestly, and refuses taps outside the safe area. The vision provider is
  injected (built-in `TemplateVision` is a PIL template matcher, fully offline).
- **No secrets** — the adb serial is configurable per device.

## Status

Component CI is green (reusable ecosystem pipeline). Security posture and
vulnerability reporting: [SECURITY.md](SECURITY.md).

## Documentation index

- **Part of:** [shesh-ecosystem](https://github.com/gaganjainse/shesh-ecosystem)
- **Compiled reading:** [shesh-docs](https://github.com/gaganjainse/shesh-docs)

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
