-- gold.fact_jobs_monthly
-- Grain: business_guid x programme_id x period_key
-- Category NULLs are converted to 0 so that SUM() works, BUT the conversion is never silent:
--   * jobs_status       - COMPLETE / PARTIAL / ALL_NULL / MISSING
--   * null_category_cnt - how many of the six categories were imputed
-- Any compliance or "jobs reported" measure must filter on jobs_status, not on total_jobs > 0.
WITH j AS (
    SELECT
        s.*,
        (CASE WHEN s.perm_full_time IS NULL THEN 1 ELSE 0 END
       + CASE WHEN s.perm_part_time IS NULL THEN 1 ELSE 0 END
       + CASE WHEN s.temp_full_time IS NULL THEN 1 ELSE 0 END
       + CASE WHEN s.temp_part_time IS NULL THEN 1 ELSE 0 END
       + CASE WHEN s.informal       IS NULL THEN 1 ELSE 0 END
       + CASE WHEN s.seasonal       IS NULL THEN 1 ELSE 0 END) AS null_category_cnt
    FROM silver.jobs s
)
SELECT
    e.business_guid,
    e.programme_id,
    e.period_key,
    e.period_label,
    j.report_number,
    COALESCE(j.perm_full_time, 0) AS perm_full_time,
    COALESCE(j.perm_part_time, 0) AS perm_part_time,
    COALESCE(j.temp_full_time, 0) AS temp_full_time,
    COALESCE(j.temp_part_time, 0) AS temp_part_time,
    COALESCE(j.informal,       0) AS informal,
    COALESCE(j.seasonal,       0) AS seasonal,
    COALESCE(j.perm_full_time, 0) + COALESCE(j.perm_part_time, 0) + COALESCE(j.temp_full_time, 0)
  + COALESCE(j.temp_part_time, 0) + COALESCE(j.informal, 0)       + COALESCE(j.seasonal, 0)       AS total_jobs,
    COALESCE(j.null_category_cnt, 6) AS null_category_cnt,
    CASE
        WHEN j.business_guid IS NULL      THEN 'MISSING'
        WHEN j.null_category_cnt = 6      THEN 'ALL_NULL'
        WHEN j.null_category_cnt > 0      THEN 'PARTIAL'
        ELSE 'COMPLETE'
    END AS jobs_status,
    j.source_run_id
FROM silver.eligibility e
LEFT JOIN j
       ON j.business_guid = e.business_guid
      AND j.period_key    = e.period_key
