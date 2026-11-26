-- severity: error
-- dimension: consistency
-- description: every latest-revision matched Bronze financial record reaches Gold with identical values (NULL-safe)
-- Note: a plain "=" treats NULL = NULL as UNKNOWN and would hide mismatches; IS DISTINCT FROM does not.
WITH src AS (
    SELECT
        f.proj_num,
        CAST(regexp_extract(f.rpt_prd_desc, 'Y([0-9]+)', 1) AS INT) + ${anchor_year} AS report_year,
        CAST(regexp_extract(f.rpt_prd_desc, 'M([0-9]+)', 1) AS INT)                  AS report_month,
        f.report_number,
        CAST(f.turnover AS DECIMAL(18, 2)) AS turnover, CAST(f.income AS DECIMAL(18, 2)) AS income,
        CAST(f.expenses AS DECIMAL(18, 2)) AS expenses, CAST(f.net_income AS DECIMAL(18, 2)) AS net_income,
        ROW_NUMBER() OVER (PARTITION BY f.proj_num, f.rpt_prd_desc ORDER BY f.report_number DESC, f.submitted_at DESC) AS rk
    FROM bronze.mne_financials_raw f
    JOIN bronze.portal_businesses b ON b.proj_num = f.proj_num
)
SELECT
    s.proj_num, s.report_year * 100 + s.report_month AS period_key, s.report_number,
    CASE WHEN g.proj_num IS NULL THEN 'MISSING_IN_GOLD' ELSE 'VALUE_MISMATCH' END AS issue
FROM src s
LEFT JOIN gold.fact_financials_monthly g
       ON g.proj_num = s.proj_num
      AND g.period_key = s.report_year * 100 + s.report_month
WHERE s.rk = 1
  AND (
        g.proj_num IS NULL
     OR s.report_number IS DISTINCT FROM g.report_number
     OR s.turnover      IS DISTINCT FROM g.turnover
     OR s.income        IS DISTINCT FROM g.income
     OR s.expenses      IS DISTINCT FROM g.expenses
     OR s.net_income    IS DISTINCT FROM g.net_income
  )
