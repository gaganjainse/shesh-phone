"""Vision→tap loop for shesh-phone.

Implements the phone-harness pattern the roadmap P1 asks for: screenshot →
locate a target via a vision provider → tap it → re-locate to verify the
action landed, retrying honestly when it did not.

The vision provider is *injected* (the README contract: "the caller supplies
an image model") so this module stays model-agnostic and fully offline-testable:
  - a real local provider (TemplateVision) does template matching on the
    screenshot with PIL — no API key, works on-device
  - anything else (an OCR model, a cloud vision API) can be passed as a
    callable with the same signature.

The loop never taps outside the phone's safe area, and reports failure
instead of pretending success.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .phone import Bounds, Phone


@dataclass(frozen=True)
class Target:
    """A located target on screen: center point + confidence."""

    x: int
    y: int
    confidence: float

    def within(self, bounds: Bounds) -> bool:
        return bounds.contains(self.x, self.y)


# A vision provider: given a screenshot path and a description of what to
# find, return the target center (or None when not found).
VisionProvider = Callable[[str, str], Target | None]


class VisionTapLoop:
    """Screenshot → locate → tap → verify, with honest retries.

    Args:
        phone: the Phone adapter (inject a fake for offline tests).
        vision: vision provider callable.
        max_attempts: how many locate→tap cycles to try before failing.
        safe_area: taps outside this area are refused.
    """

    def __init__(
        self,
        phone: Phone,
        vision: VisionProvider,
        *,
        max_attempts: int = 3,
        safe_area: Bounds | None = None,
    ) -> None:
        self.phone = phone
        self.vision = vision
        self.max_attempts = max(1, max_attempts)
        self.safe_area = safe_area or phone.safe_area

    def run(self, description: str) -> tuple[bool, str]:
        """Execute the loop. Returns (ok, summary)."""
        last_reason = ""
        for attempt in range(1, self.max_attempts + 1):
            shot_path = f"/tmp/shesh-phone-{attempt}.png"
            if not self.phone.screenshot(shot_path):
                return False, f"attempt {attempt}: screenshot failed"
            target = self.vision(shot_path, description)
            if target is None:
                last_reason = f"target '{description}' not found"
                continue  # screenshots can be flaky — retry honestly
            if not target.within(self.safe_area):
                return (
                    False,
                    f"attempt {attempt}: target at ({target.x},{target.y}) "
                    "outside safe area — refused",
                )
            res = self.phone.tap(target.x, target.y)
            if not res.ok:
                return False, f"attempt {attempt}: tap failed: {res.text}"
            # Verify the action landed: re-screenshot and re-locate.
            verify_path = "/tmp/shesh-phone-verify.png"
            if self.phone.screenshot(verify_path) and self.vision(verify_path, description) is None:
                return True, (
                    f"tapped ({target.x},{target.y}) on attempt {attempt} "
                    f"(confidence {target.confidence:.2f})"
                )
            last_reason = f"target '{description}' still present after tap on attempt {attempt}"
        return False, f"{last_reason} after {self.max_attempts} attempts"


class TemplateVision:
    """PIL-based template matcher — a real offline vision provider.

    Finds the first occurrence of a template image inside a screenshot and
    returns its center. Confidence is the best normalized correlation.
    Requires pillow; degrade to None-returning provider if it is missing.
    """

    def __init__(self, template_path: str, *, threshold: float = 0.8) -> None:
        self.template_path = template_path
        self.threshold = threshold

    def __call__(self, screenshot_path: str, description: str) -> Target | None:
        try:
            from PIL import Image, ImageChops
        except ImportError:
            return None
        try:
            screen = Image.open(screenshot_path).convert("L")
            templ = Image.open(self.template_path).convert("L")
        except OSError:
            return None
        if screen.size[0] < templ.size[0] or screen.size[1] < templ.size[1]:
            return None
        # Exhaustive template match via normalized difference.
        best: tuple[float, int, int] | None = None
        for y in range(0, screen.size[1] - templ.size[1] + 1, 2):
            for x in range(0, screen.size[0] - templ.size[0] + 1, 2):
                crop = screen.crop((x, y, x + templ.size[0], y + templ.size[1]))
                diff = ImageChops.difference(crop, templ)
                hist = diff.histogram()
                total_diff = sum(i * count for i, count in enumerate(hist))
                score = 1.0 - total_diff / (255.0 * templ.size[0] * templ.size[1])
                if best is None or score > best[0]:
                    best = (score, x, y)
        if best is None or best[0] < self.threshold:
            return None
        score, x, y = best
        return Target(
            x + templ.size[0] // 2,
            y + templ.size[1] // 2,
            round(score, 3),
        )
