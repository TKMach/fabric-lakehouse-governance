# Fabric notebook source
# nb_bronze_api_ingest
# ---------------------------------------------------------------------------------------
# Generic, replay-safe REST -> Bronze ingestion used by the scheduled survey and M&E pipelines.
#
#   * Credentials come from Azure Key Vault at run time - never stored in the notebook,
#     the pipeline JSON or Git.
#   * Every row carries lineage columns: _source, _run_id, _ingested_at, _payload.
#   * Writes are MERGE on the source's natural key, so a rerun of the same window cannot
#     duplicate submissions (idempotent by design; see docs/adr/0002).
#
# Parameters are injected by the Fabric pipeline (Notebook activity -> base parameters).
# ---------------------------------------------------------------------------------------

# PARAMETERS CELL ********************
source_name = "survey_api"                      # logical source, also the Bronze table suffix
base_url = "https://api.example.com/v1"         # sanitised; real endpoint lives in pipeline params
endpoint = "/surveys/{survey_id}/responses"
survey_id = ""
key_vault_url = "https://<your-vault>.vault.azure.net/"
secret_name = "survey-api-refresh-token"
natural_key = "response_id"                     # replay-safe merge key
since = ""                                      # ISO timestamp watermark; empty = full load
pipeline_run_id = "manual"

# CELL ********************
import json
import time
from datetime import datetime, timezone

import requests
from delta.tables import DeltaTable
from notebookutils import credentials
from pyspark.sql import functions as F
from pyspark.sql import types as T

BRONZE_TABLE = f"bronze.{source_name}_raw"
token = credentials.getSecret(key_vault_url, secret_name)   # Key Vault, resolved with the workspace identity


def fetch_all(url: str, params: dict, max_retries: int = 5) -> list[dict]:
    """Paginated GET with exponential back-off on 429/5xx. Fails loudly on auth errors."""
    rows, page = [], 1
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})
    while True:
        for attempt in range(max_retries):
            r = session.get(url, params={**params, "page": page, "per_page": 200}, timeout=60)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()             # 401/403 -> credential problem -> fail the activity
            break
        else:
            raise RuntimeError(f"{url} page {page}: retries exhausted")
        batch = r.json().get("data", [])
        rows.extend(batch)
        if len(batch) < 200:
            return rows
        page += 1


# CELL ********************
url = base_url + endpoint.format(survey_id=survey_id)
records = fetch_all(url, {"updated_since": since} if since else {})
print(f"fetched {len(records)} records from {source_name}")

schema = T.StructType([
    T.StructField(natural_key, T.StringType(), False),
    T.StructField("_payload", T.StringType(), False),
])
df = (
    spark.createDataFrame([(str(r[natural_key]), json.dumps(r)) for r in records], schema)
    .dropDuplicates([natural_key])                       # API pages can overlap
    .withColumn("_source", F.lit(source_name))
    .withColumn("_run_id", F.lit(pipeline_run_id))
    .withColumn("_ingested_at", F.lit(datetime.now(timezone.utc).isoformat()))
)

# CELL ********************
# Idempotent upsert: the same response re-delivered updates in place, never duplicates.
if spark.catalog.tableExists(BRONZE_TABLE):
    (
        DeltaTable.forName(spark, BRONZE_TABLE).alias("t")
        .merge(df.alias("s"), f"t.{natural_key} = s.{natural_key}")
        .whenMatchedUpdateAll(condition="t._payload <> s._payload")
        .whenNotMatchedInsertAll()
        .execute()
    )
else:
    df.write.format("delta").saveAsTable(BRONZE_TABLE)

version = spark.sql(f"DESCRIBE HISTORY {BRONZE_TABLE} LIMIT 1").first()["version"]

# CELL ********************
# Hand run evidence back to the pipeline (logged by the run-log activity).
notebookutils.notebook.exit(json.dumps({
    "source": source_name, "fetched": len(records), "table": BRONZE_TABLE,
    "delta_version": version, "run_id": pipeline_run_id,
}))
