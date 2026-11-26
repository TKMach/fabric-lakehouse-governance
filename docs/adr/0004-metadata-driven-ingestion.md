# ADR 0004: Metadata-driven ingestion from the operational database

**Status:** Accepted · **Date:** 2026-10

## Context
The operational portal has dozens of tables and views (businesses, programme links, finance, jobs, social and sustainability KPIs). One Copy activity per table would mean a pipeline change every time reporting needs another entity.

## Decision
- A control table (`ops.ingestion_control`) lists each entity's source query, target table, load mode, order and an enabled flag ([example](../../fabric/pipelines/ingestion_control_example.csv)).
- The pipeline runs **Lookup → ForEach (parallel, batch 4) → Copy (`@item().source_query`) → run-log script → transform + gate notebook** ([pipeline JSON](../../fabric/pipelines/pl_portal_metadata_copy.json)).
- Lineage columns are added in the Copy activity itself.
- Investigating a source discrepancy uses the **source query preview**. Preview-only SQL edits are never saved into the control table (SOP-05).

## Consequences
- Adding a source becomes a reviewed data change rather than a pipeline deployment.
- The control table becomes critical config, so it is subject to change control (SOP-09).
