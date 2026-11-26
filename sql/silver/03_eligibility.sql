-- silver.eligibility
-- The expected population: which business x programme x period SHOULD report.
-- Built from the reference reporting calendar, never from the facts themselves -
-- otherwise a month in which nobody reported would silently vanish.
SELECT
    l.business_guid,
    l.programme_id,
    l.participation_status,
    c.period_key,
    c.report_year,
    c.report_month,
    c.period_label
FROM bronze.portal_business_programmes l
CROSS JOIN bronze.ref_reporting_calendar c
WHERE c.period_key >= l.start_period_key
  AND (l.exit_period_key IS NULL OR c.period_key <= l.exit_period_key)
