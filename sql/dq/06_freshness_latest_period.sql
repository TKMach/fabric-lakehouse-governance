-- severity: error
-- dimension: freshness
-- description: the latest period in the reporting calendar has landed in Silver (a green pipeline run is not proof of fresh data)
SELECT c.period_key AS expected_latest_period, s.latest_loaded_period
FROM (SELECT MAX(period_key) AS period_key FROM bronze.ref_reporting_calendar) c
CROSS JOIN (SELECT MAX(period_key) AS latest_loaded_period FROM silver.financials WHERE match_status = 'MATCHED') s
WHERE s.latest_loaded_period IS NULL OR s.latest_loaded_period < c.period_key
