"""Basic COCOMO effort and schedule from function points (KLOC approximation)."""

from __future__ import annotations

from estimator.utils.constants import COCOMO_MODES, FP_TO_KLOC_DIVISOR


def calculate_cocomo(
    fp: float,
    mode: str,
) -> tuple[float, float, float]:
    """
    KLOC = FP / divisor (default 100).
    Effort (PM) = a * KLOC^b, TDEV = c * Effort^d.

    Returns (kloc, effort_pm, tdev_months).
    """
    if mode not in COCOMO_MODES:
        raise ValueError(f"Unknown mode: {mode}")
    if fp < 0:
        raise ValueError("FP must be non-negative")
    kloc = fp / FP_TO_KLOC_DIVISOR
    a, b, c, d = COCOMO_MODES[mode]
    if kloc <= 0:
        return 0.0, 0.0, 0.0
    effort = a * (kloc**b)
    tdev = c * (effort**d)
    return kloc, effort, tdev
