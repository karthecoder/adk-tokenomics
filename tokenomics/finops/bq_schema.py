"""
Tokenomics SDK - BigQuery Schema Auto-Provisioner
Provisions partitioned and clustered BigQuery telemetry tables and FinOps views.
"""

from typing import Optional

BIGQUERY_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.{table_id}` (
    timestamp TIMESTAMP NOT NULL,
    session_id STRING,
    app_name STRING,
    model_name STRING,
    user_query STRING,
    agent_response STRING,
    input_tokens INT64,
    cached_tokens INT64,
    output_tokens INT64,
    thinking_tokens INT64,
    total_cost FLOAT64,
    tools_called ARRAY<STRING>,
    skills_active ARRAY<STRING>,
    raw_json STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY app_name, model_name, session_id;
"""

def provision_bigquery_table(
    project_id: str,
    dataset_id: str = "bq_adk_ds",
    table_id: str = "token_consumption_logs",
    location: str = "US"
) -> bool:
    """Creates the BigQuery dataset and partitioned table if they do not exist."""
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id)
        
        # 1. Create Dataset if missing
        dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
        dataset_ref.location = location
        try:
            client.create_dataset(dataset_ref, exists_ok=True)
            print(f"[OK] Dataset {project_id}.{dataset_id} ready.", flush=True)
        except Exception as e:
            print(f"[INFO] Dataset check: {e}", flush=True)

        # 2. Create Partitioned Table
        ddl = BIGQUERY_TABLE_DDL.format(project_id=project_id, dataset_id=dataset_id, table_id=table_id)
        query_job = client.query(ddl)
        query_job.result()
        print(f"[OK] Table {project_id}.{dataset_id}.{table_id} partitioned & clustered successfully.", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to provision BigQuery table: {e}", flush=True)
        return False
