"""Tests for configurable weekly meter start days."""

import pytest

from custom_components.utility_meter_next_gen.const import WEEKLY
from custom_components.utility_meter_next_gen.sensor import (
    _build_predefined_cron_pattern,
    _resolve_week_start_day,
)


@pytest.mark.parametrize(
    ("configured_day", "language", "country", "expected"),
    [
        ("default", "en", "US", 0),
        ("default", "en", "GB", 1),
        ("default", "de", "DE", 1),
        ("sunday", "de", "DE", 0),
        ("monday", "en", "US", 1),
    ],
)
def test_resolve_week_start_day(
    configured_day: str, language: str, country: str, expected: int
) -> None:
    """Resolve explicit overrides or the locale's first weekday."""
    assert _resolve_week_start_day(configured_day, language, country) == expected


@pytest.mark.parametrize(
    ("week_start_day", "offset_days", "expected_cron"),
    [
        (0, 0, "0 0 * * 0"),
        (1, 0, "0 0 * * 1"),
        (1, 6, "0 0 * * 0"),
        (1, 8, "0 0 * * 2"),
    ],
)
def test_weekly_cron_uses_week_start_and_offset(
    week_start_day: int, offset_days: int, expected_cron: str
) -> None:
    """Apply the day offset relative to the selected week start."""
    assert (
        _build_predefined_cron_pattern(
            WEEKLY,
            {"days": offset_days, "hours": 0, "minutes": 0},
            week_start_day,
        )
        == expected_cron
    )
