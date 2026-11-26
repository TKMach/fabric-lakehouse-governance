# ADR 0005: Portable SQL transforms, tested locally in DuckDB

**Status:** Accepted · **Date:** 2026-11

## Context
Notebook-only transformation logic is hard to review and hard to test, and it often drifts away from whatever was validated. Fabric capacity is also too costly to use as a test runner.

## Decision
- Silver, Gold and DQ logic lives in **`.sql` files that are plain `SELECT`s**.
- The **runner owns materialisation**:
  - locally: `CREATE OR REPLACE TABLE … AS <select>` in DuckDB ([`runner.py`](../../src/lakehouse_gov/runner.py))
  - Fabric: `CREATE OR REPLACE TABLE … USING DELTA AS <select>` into staging schemas, gate, then promote ([`nb_transform_silver_gold.py`](../../fabric/notebooks/nb_transform_silver_gold.py))
- The SQL sticks to a shared dialect: ANSI window functions, `IS DISTINCT FROM`, and `regexp_extract` with `[0-9]` instead of `\d`. The last one matters because Spark treats a backslash in a string literal as an escape and DuckDB does not.
- DQ checks are SQL that **returns violating rows**. Zero rows means pass, and severity is declared in a header comment.
- CI runs the whole medallion on synthetic data on every push.

## Consequences
- What CI tests is exactly what Fabric runs.
- Engine-specific features (Delta MERGE, OPTIMIZE) stay in the notebooks, outside the shared SQL.
