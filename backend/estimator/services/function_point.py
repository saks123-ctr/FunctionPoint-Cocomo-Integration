"""Unadjusted / adjusted function point calculations."""

from __future__ import annotations

from estimator.utils.constants import FP_WEIGHTS, GSC_COUNT


def _complexity_triplet(counts: dict) -> tuple[int, int, int]:
    return (
        int(counts.get("simple", 0)),
        int(counts.get("average", 0)),
        int(counts.get("complex", 0)),
    )


def calculate_ufp(function_counts: dict) -> float:
    """
    function_counts: keys ei, eo, eq, ilf, eif (case-insensitive ok via normalized keys).
    Each value: {simple, average, complex} non-negative integers.
    """
    total = 0.0
    mapping = {
        "ei": "EI",
        "eo": "EO",
        "eq": "EQ",
        "ilf": "ILF",
        "eif": "EIF",
    }
    for key, fp_key in mapping.items():
        raw = function_counts.get(key) or function_counts.get(key.upper()) or {}
        s, a, c = _complexity_triplet(raw)
        w0, w1, w2 = FP_WEIGHTS[fp_key]
        total += s * w0 + a * w1 + c * w2
    return total


def calculate_caf(gsc_values: list[int]) -> float:
    if len(gsc_values) != GSC_COUNT:
        raise ValueError(f"Expected {GSC_COUNT} GSC values")
    return 0.65 + 0.01 * sum(gsc_values)


def ufp_breakdown(function_counts: dict) -> dict[str, float]:
    """Per-category contribution to UFP (before CAF)."""
    out: dict[str, float] = {}
    mapping = {
        "ei": "EI",
        "eo": "EO",
        "eq": "EQ",
        "ilf": "ILF",
        "eif": "EIF",
    }
    for key, fp_key in mapping.items():
        raw = function_counts.get(key) or function_counts.get(key.upper()) or {}
        s, a, c = _complexity_triplet(raw)
        w0, w1, w2 = FP_WEIGHTS[fp_key]
        out[fp_key] = float(s * w0 + a * w1 + c * w2)
    return out


def calculate_fp(function_counts: dict, gsc_values: list[int]) -> tuple[float, float, float]:
    """
    Returns (fp_adjusted, ufp, caf).
    """
    ufp = calculate_ufp(function_counts)
    caf = calculate_caf(gsc_values)
    fp = ufp * caf
    return fp, ufp, caf
