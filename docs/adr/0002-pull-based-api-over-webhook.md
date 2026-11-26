# ADR 0002: Scheduled API pull with Key Vault, replacing the webhook push

**Status:** Accepted · **Date:** 2026-10 · **Supersedes:** survey webhook proof of concept

## Context
The proof of concept went: survey platform → third-party webhook relay → Fabric pipeline/notebook → landing table. It worked for a demo but had three problems:
- **No replay.** A missed delivery was lost unless someone noticed.
- **An extra third party** sat in the data path, with its own credentials and uptime.
- **Hard to reconcile.** There was no single run that could be compared with the source.

## Decision
- A **scheduled Fabric pipeline pulls** responses from the survey API, filtered by an `updated_since` watermark.
- **Credentials are fetched from Azure Key Vault at run time** (`notebookutils.credentials.getSecret`). They never appear in notebooks, pipeline JSON or Git.
- Bronze writes are a **Delta MERGE on `response_id`**, so rerunning a window is idempotent ([`nb_bronze_api_ingest.py`](../../fabric/notebooks/nb_bronze_api_ingest.py)).
- Every run logs its status, the record count fetched and the resulting Delta version.

## Consequences
- Failures are recovered by rerunning the window, which is safe by construction (SOP-02).
- Snapshot row counts from a validated run serve as **evidence, not thresholds**, because survey volume legitimately grows.
- The team now owns secret rotation, which is monitored in SOP-07.
