"""Generate a deterministic synthetic dataset that reproduces the real-world failure modes
this platform was built to handle - without any real enterprise data.

Injected conditions (all counted in manifest.json so tests can assert on them):
  * businesses that did not submit a financial report        -> MISSING
  * financial records present but every value NULL           -> ALL_NULL
  * jobs records with some categories NULL                   -> PARTIAL
  * resubmissions (report_number 2 supersedes 1)             -> revision handling
  * a project number unknown to the operational portal       -> UNMATCHED
  * businesses that exited the programme mid-window          -> NOT expected after exit

Usage:  python scripts/generate_synthetic_data.py --out data/sample --seed 42
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lakehouse_gov.periods import to_label  # noqa: E402

PERIODS = [(2026, 6), (2026, 7), (2026, 8), (2026, 9)]
PROGRAMMES = {"COHORT_A": 55, "COHORT_B": 55}
JOB_CATS = ["perm_full_time", "perm_part_time", "temp_full_time", "temp_part_time", "informal", "seasonal"]
PREFIX = ["Ubuntu", "Karoo", "Protea", "Baobab", "Fynbos", "Impala", "Kestrel", "Marula", "Savanna", "Tsitsi"]
SUFFIX = ["Foods", "Logistics", "Textiles", "Digital", "Engineering", "Agri", "Cosmetics", "Construction", "Crafts", "Energy"]


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main(out: Path, seed: int):
    rnd = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    m = {"seed": seed, "periods": [y * 100 + mo for y, mo in PERIODS]}

    businesses, links = [], []
    n = 0
    for prog, size in PROGRAMMES.items():
        for _ in range(size):
            n += 1
            guid = str(uuid.UUID(int=rnd.getrandbits(128)))
            proj = f"PRJ-{1000 + n}"
            businesses.append({"business_guid": guid, "proj_num": proj,
                               "business_name": f"{rnd.choice(PREFIX)} {rnd.choice(SUFFIX)} (Pty) Ltd #{n}"})
            exited = rnd.random() < 0.05
            links.append({"business_guid": guid, "programme_id": prog,
                          "participation_status": "EXITED" if exited else "ACTIVE",
                          "start_period_key": 202606,
                          "exit_period_key": 202607 if exited else ""})

    calendar = [{"period_key": y * 100 + mo, "report_year": y, "report_month": mo, "period_label": to_label(y, mo)} for y, mo in PERIODS]

    fin, jobs = [], []
    exp = {"missing": 0, "all_null": 0, "fin_partial": 0, "jobs_partial": 0, "jobs_all_null": 0,
           "revised": 0, "eligible_rows": 0, "null_to_zero_businesses_202609": 0}
    run_id = "run-" + datetime(2026, 10, 15).strftime("%Y%m%d")

    for b, l in zip(businesses, links):
        exit_key = int(l["exit_period_key"]) if l["exit_period_key"] else None
        for y, mo in PERIODS:
            pk = y * 100 + mo
            if exit_key and pk > exit_key:
                continue  # not required after exit -> generate nothing
            exp["eligible_rows"] += 1
            r = rnd.random()
            if r < 0.06:
                exp["missing"] += 1
                continue  # no financial AND no jobs record
            submitted = datetime(y, mo, 28) + timedelta(days=rnd.randint(1, 20))
            turnover = round(rnd.uniform(80_000, 900_000), 2)
            other = round(rnd.uniform(0, 40_000), 2)
            income = round(turnover + other, 2)
            expenses = round(turnover * rnd.uniform(0.55, 0.95), 2)
            vals = {"turnover": turnover, "income": income, "expenses": expenses, "net_income": round(income - expenses, 2)}
            all_null = r < 0.09
            if all_null:
                exp["all_null"] += 1
                vals = {k: "" for k in vals}
            elif rnd.random() < 0.02:
                exp["fin_partial"] += 1
                vals["expenses"] = ""

            revised = not all_null and rnd.random() < 0.05
            base = {"proj_num": b["proj_num"], "rpt_prd_desc": to_label(y, mo)}
            if revised:
                exp["revised"] += 1
                wrong = dict(vals, turnover=round(turnover * 1.5, 2))  # superseded, wrong value
                fin.append({**base, "report_number": 1, **wrong, "submitted_at": submitted.isoformat(), "_run_id": run_id})
                submitted += timedelta(days=3)
            fin.append({**base, "report_number": 2 if revised else 1, **vals, "submitted_at": submitted.isoformat(), "_run_id": run_id})

            cats = {c: rnd.randint(0, 25) for c in JOB_CATS}
            if all_null:
                cats = {c: "" for c in JOB_CATS}
                exp["jobs_all_null"] += 1
            elif rnd.random() < 0.03:
                exp["jobs_partial"] += 1
                for c in rnd.sample(JOB_CATS, rnd.randint(1, 4)):
                    cats[c] = ""
            if pk == 202609 and any(v == "" for v in cats.values()):
                exp["null_to_zero_businesses_202609"] += 1
            jobs.append({**base, "report_number": 2 if revised else 1, **cats, "submitted_at": submitted.isoformat(), "_run_id": run_id})

    # a submission for a project the portal does not know about -> UNMATCHED
    fin.append({"proj_num": "PRJ-9999", "rpt_prd_desc": to_label(2026, 9), "report_number": 1, "turnover": 100000.0,
                "income": 100000.0, "expenses": 90000.0, "net_income": 10000.0, "submitted_at": "2026-10-02T00:00:00", "_run_id": run_id})
    exp["unmatched"] = 1

    write_csv(out / "portal_businesses.csv", businesses)
    write_csv(out / "portal_business_programmes.csv", links)
    write_csv(out / "ref_reporting_calendar.csv", calendar)
    write_csv(out / "mne_financials_raw.csv", fin)
    write_csv(out / "mne_jobs_raw.csv", jobs)
    m["expected"] = exp
    (out / "manifest.json").write_text(json.dumps(m, indent=2))
    print(f"wrote {len(businesses)} businesses, {len(fin)} financial rows, {len(jobs)} jobs rows -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/sample"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    main(a.out, a.seed)
