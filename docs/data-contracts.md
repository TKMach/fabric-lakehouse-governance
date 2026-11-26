# Data contracts

| Domain | Standard |
|---|---|
| **Business identity** | Use the canonical `business_guid` wherever possible. Source IDs (`proj_num`, portal ID, CRM ID) are kept for traceability. Unresolved IDs → `match_status = 'UNMATCHED'`, surfaced and never dropped |
| **Programme identity** | `programme_id`, programme group and `participation_status` are always explicit. Exit dates bound the eligible population |
| **Reporting period** | Source labels are mapped to `report_year`, `report_month` and `period_key` (YYYYMM). **The original label is kept** (`period_label`) |
| **Grain** | Declared at the top of every Gold SQL file and enforced by a uniqueness check. Business × programme × month for facts; contact, and contact × programme, for CRM |
| **Revisions** | The latest accepted record per (source key, period) is chosen by `report_number DESC, submitted_at DESC`. Superseded records stay in Bronze |
| **Missing vs zero** | See [ADR 0003](adr/0003-absent-is-not-zero.md). Financials: NULL is preserved, plus `submission_status`. Jobs: NULL → 0 for sums, plus `jobs_status` and `null_category_cnt` |
| **Source-reported measures** | Measures such as `net_income` are taken from the source and **never re-derived** downstream |
| **Consent & privacy** | CRM unsubscribe and marketing opt-out are authoritative. Personal data gets least-privilege access, and exports are restricted |
| **Lineage** | Source → pipeline run (`_run_id`) → Bronze → Silver → Gold → semantic measure, traceable by run ID and Delta version |

## Consuming Gold correctly

```sql
-- Turnover with the population it covers
SELECT programme_id, period_key,
       SUM(turnover)                                          AS turnover_reported,
       COUNT(*)                                               AS eligible,
       SUM(CASE WHEN submission_status = 'SUBMITTED' THEN 1 ELSE 0 END) AS submitted
FROM gold.fact_financials_monthly
GROUP BY programme_id, period_key;

-- Non-reporter list: straight from Gold
SELECT business_guid, programme_id, period_key
FROM gold.fact_financials_monthly
WHERE submission_status = 'MISSING';

-- WRONG: treats "did not report" as "reported zero"
-- SELECT COUNT(*) FROM gold.fact_jobs_monthly WHERE total_jobs > 0;
```
