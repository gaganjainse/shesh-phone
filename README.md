# shesh-phone

> **ADB control for an Android phone** (target: Realme Narzo on CachyOS). Safe-bounds
> tapping, swipes, text input, screenshots, and app launching — with all `adb`
> calls injectable so it is fully testable offline.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python) ![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue) ![CI](https://github.com/gaganjainse/shesh-phone/actions/workflows/ci.yml/badge.svg)

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

> **Reproducible install:** `uv.lock` pins the full dependency tree. Install with
> `uv sync --frozen` (or `uv pip install -r <(uv export --frozen)`) for a locked build.

## Status

Component CI is green (reusable ecosystem pipeline). Security posture and
vulnerability reporting: [SECURITY.md](SECURITY.md).

## Documentation index

- **Part of:** [shesh-ecosystem](https://github.com/gaganjainse/shesh-ecosystem)
- **Compiled reading:** [shesh-docs](https://github.com/gaganjainse/shesh-docs)

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
