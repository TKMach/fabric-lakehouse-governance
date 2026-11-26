-- silver.jobs
-- Grain: one row per proj_num x reporting period (latest accepted revision).
-- NULL category values are preserved; Gold decides how to aggregate them.
WITH parsed AS (
    SELECT
        j.*,
        CAST(regexp_extract(j.rpt_prd_desc, 'Y([0-9]+)', 1) AS INT) + ${anchor_year} AS report_year,
        CAST(regexp_extract(j.rpt_prd_desc, 'M([0-9]+)', 1) AS INT)                  AS report_month
    FROM bronze.mne_jobs_raw j
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
    r.report_year * 100 + r.report_month    AS period_key,
    CAST(r.perm_full_time AS INT)           AS perm_full_time,
    CAST(r.perm_part_time AS INT)           AS perm_part_time,
    CAST(r.temp_full_time AS INT)           AS temp_full_time,
    CAST(r.temp_part_time AS INT)           AS temp_part_time,
    CAST(r.informal       AS INT)           AS informal,
    CAST(r.seasonal       AS INT)           AS seasonal,
    r.submitted_at,
    r._run_id                               AS source_run_id
FROM ranked r
LEFT JOIN bronze.portal_businesses b
       ON r.proj_num = b.proj_num
WHERE r.revision_rank = 1
