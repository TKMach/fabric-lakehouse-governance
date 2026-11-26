# Data quality framework

Each check is a SQL file in [`sql/dq/`](../sql/dq) that **returns the violating rows**. Zero rows means pass. Each file declares its severity and dimension in header comments:

```sql
-- severity: error
-- dimension: consistency
-- description: every latest-revision matched Bronze financial record reaches Gold with identical values (NULL-safe)
```

An error-severity failure **blocks promotion of Gold**. A warn-severity failure is logged and reported. Every gate decision is appended to `ops.dq_results` with its run ID.

| Dimension | Question | Checks |
|---|---|---|
| Completeness | Did every expected business, contact or response arrive? | `eligible_population_not_empty`, `unmatched_source_records` (warn); Gold row per eligible business |
| Uniqueness | Is the declared grain actually unique? | `gold_financials_grain_unique`, `gold_jobs_grain_unique` |
| Validity | Are types, statuses and period labels legal? | Typed casts in Silver; period parser rejects malformed labels |
| Consistency | Does Gold equal the source? | `recon_financials_bronze_to_gold` (NULL-safe `IS DISTINCT FROM`), `recon_jobs_no_value_changed` |
| Freshness | Has the latest **business period** landed, not just the latest run? | `freshness_latest_period` |
| Traceability | Can every row be traced back? | Lineage columns, `source_run_id`, Delta version in run log |

## Proving the gate works

The test suite doesn't stop at "everything passes". It also **corrupts Gold on purpose** and asserts that the gate fails:

- `test_gate_catches_a_tampered_gold_value`: changes one turnover value by R0.01 and expects the reconciliation check to fail.
- `test_gate_catches_a_duplicated_grain`: duplicates one row and expects the uniqueness check to fail.

A check that has never been seen to fail isn't a control.
