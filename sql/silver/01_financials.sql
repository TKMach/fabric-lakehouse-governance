-- silver.financials
-- Grain: one row per proj_num x reporting period (latest accepted revision).
-- Contract: period label parsed (original retained); identity resolved to business_guid;
--           NULLs preserved exactly as submitted - no imputation in Silver.
-- Portable: runs unchanged on Fabric Spark SQL and DuckDB (no backslash regex, ANSI window fns).
WITH parsed AS (
    SELECT
        f.*,
        CAST(regexp_extract(f.rpt_prd_desc, 'Y([0-9]+)', 1) AS INT) + ${anchor_year} AS report_year,
        CAST(regexp_extract(f.rpt_prd_desc, 'M([0-9]+)', 1) AS INT)                  AS report_month
    FROM bronze.mne_financials_raw f
),
ranked AS (
    SELECT
        p.*,
        ROW_NUMBER() OVER (
            PARTITION BY p.proj_num, p.report_year, p.report_month
            ORDER BY p.report_number DESC, p.submitted_at DESC
        ) AS revision_rank
    FROM parsed p
)
SELECT
    r.proj_num,
    b.business_guid,
    CASE WHEN b.business_guid IS NULL THEN 'UNMATCHED' ELSE 'MATCHED' END AS match_status,
    r.report_number,
    r.rpt_prd_desc                          AS period_label,
    r.report_year,
    r.report_month,
    r.report_year * 100 + r.report_month    AS period_key,
    CAST(r.turnover   AS DECIMAL(18, 2))    AS turnover,
    CAST(r.income     AS DECIMAL(18, 2))    AS income,
    CAST(r.expenses   AS DECIMAL(18, 2))    AS expenses,
    CAST(r.net_income AS DECIMAL(18, 2))    AS net_income,   -- source-reported; never recomputed
    r.submitted_at,
    r._run_id                               AS source_run_id
FROM ranked r
LEFT JOIN bronze.portal_businesses b
       ON r.proj_num = b.proj_num
WHERE r.revision_rank = 1
