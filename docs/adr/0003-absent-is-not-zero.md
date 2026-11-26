# ADR 0003: An absent record is not a zero

**Status:** Accepted · **Date:** 2026-11

## Context
Reconciling the reference month across two cohorts showed that every Bronze → Gold jobs difference was a **NULL converted to 0**. No reported value had been changed. That is numerically fine for sums. But it meant a business that **did not report** looked the same on a dashboard as one that **reported zero jobs**, and a missing financial row looked like zero turnover.

There were actually five different situations, and all of them were being displayed as "0" or as blank:

| Situation | Example |
|---|---|
| No record at all | business did not submit |
| Record exists, every value NULL | blank form submitted |
| Record exists, some values NULL | 2 of 6 jobs categories filled |
| Genuine reported zero | business truly had no temporary staff |
| Not required | business exited the programme |

## Decision
1. **Gold rows are driven by the eligible population** (`silver.eligibility`), not by the facts. Every business expected to report has a row whether or not it did. The population is built from a *reference calendar*, so a month in which nobody reported still appears.
2. **Financial values stay NULL** in Gold when they were not reported. Each row carries a `submission_status`: `SUBMITTED / PARTIAL / ALL_NULL / MISSING`.
3. **Jobs categories may be COALESCEd to 0** so that SUM works, but each row carries `jobs_status` and `null_category_cnt`. Compliance measures filter on status, never on `total_jobs > 0`.
4. The rules are implemented once in SQL and once as a reference in Python ([`exceptions.py`](../../src/lakehouse_gov/exceptions.py)). A test asserts the two agree row by row.

## Consequences
- Dashboards can show "X of Y businesses reported" next to every total.
- Non-reporter lists come straight from Gold (`submission_status = 'MISSING'`).
- Analysts need to know which column to filter on. This is documented in [data contracts](../data-contracts.md).
