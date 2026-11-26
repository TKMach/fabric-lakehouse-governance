-- severity: warn
-- dimension: completeness
-- description: submissions whose project number cannot be resolved to a canonical business_guid (excluded from Gold until mapped)
SELECT proj_num, period_key, 'financials' AS source FROM silver.financials WHERE match_status = 'UNMATCHED'
UNION ALL
SELECT proj_num, period_key, 'jobs'       AS source FROM silver.jobs       WHERE match_status = 'UNMATCHED'
