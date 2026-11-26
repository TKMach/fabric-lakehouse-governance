-- gold.fact_financials_monthly
-- Grain: business_guid x programme_id x period_key  (unique - enforced by dq/gold_grain_unique)
-- Every ELIGIBLE row exists, whether or not the business reported.
-- Financial values stay NULL when not reported: an absent record is not zero turnover.
SELECT
    e.business_guid,
    e.programme_id,
    e.period_key,
    e.report_year,
    e.report_month,
    e.period_label,
    f.proj_num,
    f.report_number,
    f.turnover,
    f.income,
    f.expenses,
    f.net_income,
    CASE
        WHEN f.business_guid IS NULL THEN 'MISSING'
        WHEN f.turnover IS NULL AND f.income IS NULL AND f.expenses IS NULL AND f.net_income IS NULL THEN 'ALL_NULL'
        WHEN f.turnover IS NULL OR  f.income IS NULL OR  f.expenses IS NULL OR  f.net_income IS NULL THEN 'PARTIAL'
        ELSE 'SUBMITTED'
    END AS submission_status,
    f.source_run_id
FROM silver.eligibility e
LEFT JOIN silver.financials f
       ON f.business_guid = e.business_guid
      AND f.period_key    = e.period_key
