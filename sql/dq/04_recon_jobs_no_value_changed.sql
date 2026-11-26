-- severity: error
-- dimension: consistency
-- description: Gold may turn a NULL jobs category into 0, but must never change a reported (non-NULL) value
SELECT s.proj_num, s.period_key
FROM silver.jobs s
JOIN gold.fact_jobs_monthly g
  ON g.business_guid = s.business_guid
 AND g.period_key    = s.period_key
WHERE (s.perm_full_time IS NOT NULL AND s.perm_full_time <> g.perm_full_time)
   OR (s.perm_part_time IS NOT NULL AND s.perm_part_time <> g.perm_part_time)
   OR (s.temp_full_time IS NOT NULL AND s.temp_full_time <> g.temp_full_time)
   OR (s.temp_part_time IS NOT NULL AND s.temp_part_time <> g.temp_part_time)
   OR (s.informal       IS NOT NULL AND s.informal       <> g.informal)
   OR (s.seasonal       IS NOT NULL AND s.seasonal       <> g.seasonal)
