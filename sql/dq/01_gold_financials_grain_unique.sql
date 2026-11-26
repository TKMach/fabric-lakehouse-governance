-- severity: error
-- dimension: uniqueness
-- description: gold.fact_financials_monthly has exactly one row per business x programme x period
SELECT business_guid, programme_id, period_key, COUNT(*) AS n
FROM gold.fact_financials_monthly
GROUP BY business_guid, programme_id, period_key
HAVING COUNT(*) > 1
