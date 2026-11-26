"""Submission / completeness classification.

The single most important semantic rule on this platform:

    **An absent record is not a zero.**

Gold jobs tables convert missing category values to 0 so that sums work, but every
row also carries a completeness status so that reports can distinguish
"reported zero jobs" from "did not report". This module is the reference
implementation of that classification; ``sql/gold/*.sql`` implements the same
rules set-based and ``tests/`` keep the two in step.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Sequence


class FinancialStatus(str, Enum):
    SUBMITTED = "SUBMITTED"          # record present, key values populated
    ALL_NULL = "ALL_NULL"            # record present, every key financial value NULL
    PARTIAL = "PARTIAL"              # record present, some key values NULL
    MISSING = "MISSING"              # expected (eligible) but no record at all
    NOT_REQUIRED = "NOT_REQUIRED"    # exited / not eligible for the period


class JobsStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    ALL_NULL = "ALL_NULL"
    MISSING = "MISSING"
    NOT_REQUIRED = "NOT_REQUIRED"


def classify_financial(record_present: bool, values: Sequence[Optional[float]], eligible: bool = True) -> FinancialStatus:
    if not eligible:
        return FinancialStatus.NOT_REQUIRED
    if not record_present:
        return FinancialStatus.MISSING
    nulls = sum(v is None for v in values)
    if nulls == len(values):
        return FinancialStatus.ALL_NULL
    if nulls:
        return FinancialStatus.PARTIAL
    return FinancialStatus.SUBMITTED


def classify_jobs(record_present: bool, categories: Sequence[Optional[int]], eligible: bool = True) -> JobsStatus:
    if not eligible:
        return JobsStatus.NOT_REQUIRED
    if not record_present:
        return JobsStatus.MISSING
    nulls = sum(c is None for c in categories)
    if nulls == len(categories):
        return JobsStatus.ALL_NULL
    if nulls:
        return JobsStatus.PARTIAL
    return JobsStatus.COMPLETE
