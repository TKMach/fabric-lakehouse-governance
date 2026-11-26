-- severity: error
-- dimension: completeness
-- description: every reporting-calendar period has a non-empty expected population
SELECT c.period_key
FROM bronze.ref_reporting_calendar c
LEFT JOIN silver.eligibility e ON e.period_key = c.period_key
GROUP BY c.period_key
HAVING COUNT(e.business_guid) = 0
