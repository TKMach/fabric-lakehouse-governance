# Fabric notebook source
# nb_transform_silver_gold
# ---------------------------------------------------------------------------------------
# Runs the same SQL files that are unit-tested locally (sql/silver, sql/gold, sql/dq)
# against the Fabric Lakehouse, materialising each as a Delta table.
#
# Gate semantics: Silver and Gold are built into the *_staging schemas first; Gold is only
# swapped into the reporting schema if every error-severity DQ check returns zero rows.
# A failed gate leaves yesterday's Gold untouched and fails the pipeline activity.
# ---------------------------------------------------------------------------------------

# PARAMETERS CELL ********************
sql_root = "Files/sql"            # repo sql/ folder synced to the Lakehouse Files area
anchor_year = 2012                # validated: "Y14 M9" == 2026-09
pipeline_run_id = "manual"

# CELL ********************
import json
import re

from notebookutils import fs

params = {"anchor_year": anchor_year}


def read(path: str) -> str:
    return fs.head(path, 1_000_000)


def render(sql: str) -> str:
    for k, v in params.items():
        sql = sql.replace("${" + k + "}", str(v))
    assert "${" not in sql, "unresolved parameter"
    return sql


def files(layer: str) -> list[str]:
    return sorted(f.path for f in fs.ls(f"{sql_root}/{layer}") if f.name.endswith(".sql"))


def name_of(path: str) -> str:
    return re.sub(r"^\d+_", "", path.rsplit("/", 1)[-1][:-4])


# CELL ********************
# Build into staging. SQL references silver./gold. - point those names at staging for this run.
for layer in ("silver", "gold"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {layer}_staging")

built = []
for layer in ("silver", "gold"):
    for f in files(layer):
        sql = render(read(f)).replace("silver.", "silver_staging.").replace("gold.", "gold_staging.")
        target = f"{layer}_staging.{name_of(f)}"
        spark.sql(f"CREATE OR REPLACE TABLE {target} USING DELTA AS {sql}")
        built.append(target)
print("built:", built)

# CELL ********************
results = []
for f in files("dq"):
    raw = read(f)
    sql = render(raw).replace("silver.", "silver_staging.").replace("gold.", "gold_staging.")
    sev = re.search(r"--\s*severity:\s*(\w+)", raw).group(1)
    n = spark.sql(f"SELECT COUNT(*) AS n FROM ({sql}) v").first()["n"]
    results.append({"check": name_of(f), "severity": sev, "violations": n})

spark.createDataFrame(results).selectExpr("*", f"'{pipeline_run_id}' AS run_id", "current_timestamp() AS checked_at") \
    .write.mode("append").saveAsTable("ops.dq_results")          # audit trail of every gate decision

failed = [r for r in results if r["severity"] == "error" and r["violations"] > 0]

# CELL ********************
if failed:
    raise Exception(f"DQ gate failed - Gold NOT published: {json.dumps(failed)}")

# Promote: copy validated staging tables into the reporting schemas
for t in built:
    layer, name = t.split("_staging.")
    spark.sql(f"CREATE OR REPLACE TABLE {layer}.{name} USING DELTA AS SELECT * FROM {t}")

notebookutils.notebook.exit(json.dumps({"published": built, "checks": results, "run_id": pipeline_run_id}))
