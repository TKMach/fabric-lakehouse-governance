-- gold.kpi_programme_month
-- Reporting-ready summary. Sums only count reported values, and every sum is published
-- next to the population it was computed over, so a "low" number can be explained.
SELECT
    f.programme_id,
    f.period_key,
    COUNT(*)                                                         AS eligible_businesses,
    SUM(CASE WHEN f.submission_status = 'SUBMITTED' THEN 1 ELSE 0 END) AS fin_submitted,
    SUM(CASE WHEN f.submission_status = 'PARTIAL'   THEN 1 ELSE 0 END) AS fin_partial,
    SUM(CASE WHEN f.submission_status = 'ALL_NULL'  THEN 1 ELSE 0 END) AS fin_all_null,
    SUM(CASE WHEN f.submission_status = 'MISSING'   THEN 1 ELSE 0 END) AS fin_missing,
    SUM(f.turnover)                                                  AS turnover,
    SUM(f.net_income)                                                AS net_income,
    SUM(j.total_jobs)                                                AS total_jobs,
    SUM(CASE WHEN j.jobs_status = 'COMPLETE' THEN 1 ELSE 0 END)      AS jobs_complete
FROM gold.fact_financials_monthly f
JOIN gold.fact_jobs_monthly j
  ON j.business_guid = f.business_guid
 AND j.programme_id  = f.programme_id
 AND j.period_key    = f.period_key
GROUP BY f.programme_id, f.period_key
