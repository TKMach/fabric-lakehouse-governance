"""Local medallion runner (DuckDB).

The SQL in ``sql/`` is written as plain SELECT statements that run unchanged on
Fabric Spark SQL and on DuckDB. The *runner* owns materialisation:

* locally  ->  ``CREATE OR REPLACE TABLE <layer>.<name> AS <select>``   (this module)
* Fabric   ->  ``CREATE OR REPLACE TABLE <layer>.<name> USING DELTA AS <select>``
               (``fabric/notebooks/nb_transform_silver_gold.py``)

So the business logic that is unit-tested here is byte-for-byte the logic deployed.

Usage:
    python -m lakehouse_gov.runner --data data/sample            # build + DQ gate
    python -m lakehouse_gov.runner --data data/sample --report   # also print KPI table
Exit code 1 if any error-severity data-quality check fails.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb

from .periods import DEFAULT_ANCHOR_YEAR

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
BRONZE_TABLES = [
    "portal_businesses",
    "portal_business_programmes",
    "ref_reporting_calendar",
    "mne_financials_raw",
    "mne_jobs_raw",
]


def render(sql: str, params: dict) -> str:
    for k, v in params.items():
        sql = sql.replace("${" + k + "}", str(v))
    if "${" in sql:
        raise ValueError(f"unresolved parameter in SQL: {re.findall(r'\$\{[^}]+\}', sql)}")
    return sql


def table_name(path: Path) -> str:
    """'01_fact_financials_monthly.sql' -> 'fact_financials_monthly'"""
    return re.sub(r"^\d+_", "", path.stem)


@dataclass
class CheckResult:
    name: str
    severity: str
    dimension: str
    description: str
    violations: int

    @property
    def passed(self) -> bool:
        return self.violations == 0


def _meta(sql: str, key: str, default: str = "") -> str:
    m = re.search(rf"^--\s*{key}:\s*(.+)$", sql, re.MULTILINE)
    return m.group(1).strip() if m else default


class LocalLakehouse:
    def __init__(self, params: dict | None = None, db: str = ":memory:"):
        self.con = duckdb.connect(db)
        self.params = {"anchor_year": DEFAULT_ANCHOR_YEAR, **(params or {})}
        for layer in ("bronze", "silver", "gold"):
            self.con.execute(f"CREATE SCHEMA IF NOT EXISTS {layer}")

    # ---- Bronze: land source extracts as-is --------------------------------------------
    def load_bronze(self, data_dir: Path):
        for t in BRONZE_TABLES:
            f = Path(data_dir) / f"{t}.csv"
            self.con.execute(
                f"CREATE OR REPLACE TABLE bronze.{t} AS "
                f"SELECT * FROM read_csv('{f.as_posix()}', header=true, nullstr='', auto_detect=true)"
            )

    # ---- Silver / Gold: run SELECTs in file order, runner materialises ------------------
    def build_layer(self, layer: str) -> list[str]:
        built = []
        for f in sorted((SQL_DIR / layer).glob("*.sql")):
            name = table_name(f)
            sql = render(f.read_text(), self.params)
            self.con.execute(f"CREATE OR REPLACE TABLE {layer}.{name} AS {sql}")
            built.append(f"{layer}.{name}")
        return built

    def build(self, data_dir: Path) -> list[str]:
        self.load_bronze(data_dir)
        return self.build_layer("silver") + self.build_layer("gold")

    # ---- Data-quality gate --------------------------------------------------------------
    def run_checks(self) -> list[CheckResult]:
        out = []
        for f in sorted((SQL_DIR / "dq").glob("*.sql")):
            raw = f.read_text()
            sql = render(raw, self.params)
            n = self.con.execute(f"SELECT COUNT(*) FROM ({sql}) v").fetchone()[0]
            out.append(CheckResult(table_name(f), _meta(raw, "severity", "error"), _meta(raw, "dimension"), _meta(raw, "description"), n))
        return out

    def query(self, sql: str):
        return self.con.execute(sql).fetchall()


def _print_checks(results: list[CheckResult]):
    print("\nDATA QUALITY GATE")
    print("-" * 96)
    for r in results:
        status = "PASS" if r.passed else ("FAIL" if r.severity == "error" else "WARN")
        print(f"[{status}] {r.dimension:<12} {r.name:<40} violations={r.violations}")
    print("-" * 96)


def _print_kpis(lh: LocalLakehouse):
    rows = lh.query("SELECT * FROM gold.kpi_programme_month ORDER BY programme_id, period_key")
    hdr = ("programme", "period", "eligible", "submitted", "partial", "all_null", "missing", "turnover", "jobs", "jobs_complete")
    print("\nGOLD KPI SUMMARY")
    print(" ".join(f"{h:>13}" for h in hdr))
    for r in rows:
        prog, pk, el, sub, part, alln, miss, turn, _ni, jobs, jc = r
        print(" ".join(f"{v:>13}" for v in (prog, pk, el, sub, part, alln, miss, f"{float(turn or 0):,.0f}", jobs, jc)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "sample")
    ap.add_argument("--report", action="store_true", help="print the Gold KPI summary")
    a = ap.parse_args(argv)

    lh = LocalLakehouse()
    built = lh.build(a.data)
    print("Built:", ", ".join(built))
    results = lh.run_checks()
    _print_checks(results)
    if a.report:
        _print_kpis(lh)
    failed = [r for r in results if not r.passed and r.severity == "error"]
    if failed:
        print(f"\nGATE FAILED: {len(failed)} error-level check(s). Gold must not be published.")
        return 1
    print("\nGATE PASSED: Gold is publishable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
