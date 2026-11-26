"""End-to-end: build the medallion on synthetic data and prove the governance rules hold."""
from lakehouse_gov.exceptions import classify_financial, classify_jobs


def test_quality_gate_passes(lakehouse):
    results = {r.name: r for r in lakehouse.run_checks()}
    errors = [r for r in results.values() if r.severity == "error" and not r.passed]
    assert not errors, errors
    assert results["unmatched_source_records"].violations == 1  # surfaced as a warning


def test_gold_has_a_row_for_every_eligible_business(lakehouse, dataset):
    _, exp = dataset
    (n,) = lakehouse.query("SELECT COUNT(*) FROM gold.fact_financials_monthly")[0]
    assert n == exp["eligible_rows"]


def test_missing_and_all_null_are_counted_not_zeroed(lakehouse, dataset):
    _, exp = dataset
    got = dict(lakehouse.query("SELECT submission_status, COUNT(*) FROM gold.fact_financials_monthly GROUP BY 1"))
    assert got.get("MISSING", 0) == exp["missing"]
    assert got.get("ALL_NULL", 0) == exp["all_null"]
    assert got.get("PARTIAL", 0) == exp["fin_partial"]
    # financial values are NULL - not 0 - when nothing was reported
    (zeros,) = lakehouse.query("SELECT COUNT(*) FROM gold.fact_financials_monthly WHERE submission_status='MISSING' AND turnover IS NOT NULL")[0]
    assert zeros == 0


def test_jobs_null_to_zero_is_flagged(lakehouse, dataset):
    _, exp = dataset
    got = dict(lakehouse.query("SELECT jobs_status, COUNT(*) FROM gold.fact_jobs_monthly GROUP BY 1"))
    assert got.get("PARTIAL", 0) == exp["jobs_partial"]
    assert got.get("ALL_NULL", 0) == exp["jobs_all_null"]
    (n,) = lakehouse.query("SELECT COUNT(*) FROM gold.fact_jobs_monthly WHERE period_key=202609 AND jobs_status IN ('PARTIAL','ALL_NULL')")[0]
    assert n == exp["null_to_zero_businesses_202609"]


def test_latest_revision_wins(lakehouse, dataset):
    _, exp = dataset
    (n,) = lakehouse.query("SELECT COUNT(*) FROM gold.fact_financials_monthly WHERE report_number = 2")[0]
    assert n == exp["revised"]


def test_sql_and_python_classification_agree(lakehouse):
    rows = lakehouse.query("""
        SELECT g.submission_status, f.business_guid IS NOT NULL, f.turnover, f.income, f.expenses, f.net_income
        FROM gold.fact_financials_monthly g
        LEFT JOIN silver.financials f ON f.business_guid = g.business_guid AND f.period_key = g.period_key""")
    for status, present, *vals in rows:
        assert classify_financial(present, vals).value == status
    jrows = lakehouse.query("""
        SELECT g.jobs_status, s.business_guid IS NOT NULL, s.perm_full_time, s.perm_part_time, s.temp_full_time,
               s.temp_part_time, s.informal, s.seasonal
        FROM gold.fact_jobs_monthly g
        LEFT JOIN silver.jobs s ON s.business_guid = g.business_guid AND s.period_key = g.period_key""")
    for status, present, *cats in jrows:
        assert classify_jobs(present, cats).value == status


def test_gate_catches_a_tampered_gold_value(lakehouse):
    """The reconciliation check must actually bite - corrupt one value and expect a failure."""
    lakehouse.con.execute("""
        UPDATE gold.fact_financials_monthly SET turnover = turnover + 0.01
        WHERE rowid = (SELECT MIN(rowid) FROM gold.fact_financials_monthly WHERE submission_status='SUBMITTED')""")
    results = {r.name: r for r in lakehouse.run_checks()}
    assert results["recon_financials_bronze_to_gold"].violations == 1


def test_gate_catches_a_duplicated_grain(lakehouse):
    lakehouse.con.execute("INSERT INTO gold.fact_jobs_monthly SELECT * FROM gold.fact_jobs_monthly LIMIT 1")
    results = {r.name: r for r in lakehouse.run_checks()}
    assert not results["gold_jobs_grain_unique"].passed
