"""Reporting-period parsing.

The M&E platform labels reporting periods relative to a programme anchor year,
e.g. ``"Y14 M9"``. A naive calendar-text filter (``LIKE '%Sep%'``) silently returns
zero rows, which is how a "missing September" incident was first misdiagnosed.

Rules:
* Parse the label into (year, month) using a configured anchor year.
* Never drop the original label - it is retained in Silver for traceability.
* Unparseable labels are surfaced, not coerced.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Validated against a reference period: "Y14 M9" == September 2026  ->  anchor = 2012
DEFAULT_ANCHOR_YEAR = 2012

_LABEL = re.compile(r"^\s*Y(?P<y>\d{1,3})\s*M(?P<m>\d{1,2})\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Period:
    year: int
    month: int
    label: str

    @property
    def key(self) -> int:
        """Sortable integer key, e.g. 202609."""
        return self.year * 100 + self.month


class PeriodParseError(ValueError):
    pass


def parse_period(label: str, anchor_year: int = DEFAULT_ANCHOR_YEAR) -> Period:
    if label is None:
        raise PeriodParseError("period label is NULL")
    m = _LABEL.match(label)
    if not m:
        raise PeriodParseError(f"unrecognised period label: {label!r}")
    month = int(m.group("m"))
    if not 1 <= month <= 12:
        raise PeriodParseError(f"month out of range in {label!r}")
    return Period(year=anchor_year + int(m.group("y")), month=month, label=label)


def to_label(year: int, month: int, anchor_year: int = DEFAULT_ANCHOR_YEAR) -> str:
    """Inverse of :func:`parse_period` - used by the synthetic data generator and tests."""
    return f"Y{year - anchor_year} M{month}"
