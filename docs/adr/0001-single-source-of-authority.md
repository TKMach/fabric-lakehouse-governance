# ADR 0001: One authoritative source per reporting domain

**Status:** Accepted · **Date:** 2026-10

## Context
Financials for the active cohorts reached the Lakehouse by two routes:
1. a **legacy view** in the operational Azure SQL database (`legacy.vw_financials`), and
2. the **M&E platform's direct API**.

The legacy view was missing whole months for one cohort (row counts fell month on month and reached zero for the latest two months). People first assumed the Fabric Copy activity was losing rows. I compared a source-side query preview with the landed Bronze table and they matched exactly. That proved the gap was **upstream coverage, not pipeline loss**. Meanwhile the direct API held complete data for the same months.

Enriched tables built on the legacy path also had duplicate business-month groups.

## Decision
- Each reporting domain has **exactly one authoritative source**, recorded in a source-of-authority matrix (see [architecture](../architecture.md#source-of-authority)).
- For the active cohorts, the direct API → Gold path is authoritative. The legacy path is kept for historical cohorts only.
- Tables on the legacy path are labelled **not authoritative** in the object inventory and are never promoted.
- The two paths are **never unioned** unless business key, period and duplicate controls are in place.

## Consequences
- Reports have one obvious place to read each metric.
- Debugging starts at the source before the pipeline, which is now SOP-05.
- Legacy tables can be decommissioned on a schedule instead of lingering.
