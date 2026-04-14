"""Shared display formatting for reports and API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone
from django.utils.dateformat import format as django_format


def format_decimal(value: Any, places: int = 2) -> str:
    """Format a numeric value with a fixed number of decimal places."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{n:.{places}f}"


def format_datetime(value: Any) -> str:
    """
    Format a datetime (aware/naive) or ISO string for human-readable reports.
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            # fromisoformat handles ...Z in 3.11+
            text = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(text)
        except ValueError:
            return value
    elif isinstance(value, datetime):
        dt = value
    else:
        return str(value)

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    dt = timezone.localtime(dt)
    return django_format(dt, "N j, Y, P T")


def format_cocomo_mode(mode: str | None) -> str:
    """Human-readable COCOMO mode label."""
    if not mode:
        return "—"
    labels = {
        "organic": "Organic",
        "semi_detached": "Semi-detached",
        "embedded": "Embedded",
    }
    return labels.get(mode, mode.replace("_", " ").title())
