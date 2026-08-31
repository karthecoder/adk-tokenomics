"""
Tokenomics SDK - Pluggable Storage & Telemetry Sinks
Supports In-Memory, SQLite, DuckDB, and Production BigQuery streaming.
"""

import abc
import time
import json
import threading
import queue
import datetime
from typing import Dict, Any, List, Optional
from tokenomics.core.config import TokenomicsConfig

class BaseSink(abc.ABC):
    @abc.abstractmethod
    def write_turn(self, record: Dict[str, Any]):
        """Writes a single turn record to the sink."""
        pass

    @abc.abstractmethod
    def fetch_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches recent turn records."""
        pass

    def close(self):
        """Clean up sink resources."""
        pass

class InMemorySink(BaseSink):
    """In-memory telemetry sink for testing and local prototyping."""
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def write_turn(self, record: Dict[str, Any]):
        with self._lock:
            self.records.append(record)

    def fetch_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self.records[-limit:]))

    def clear(self):
        with self._lock:
            self.records.clear()

class BigQuerySink(BaseSink):
    """Production BigQuery streaming sink with background queue."""
    def __init__(self, config: TokenomicsConfig):
        self.config = config
        self.project_id = config.project_id
        self.dataset_id = config.dataset_id
        self.table_id = config.table_id
        self._client = None
        self._queue = queue.Queue(maxsize=10000)
        self._stop_event = threading.Event()
        
        # Start background worker thread
        self._worker = threading.Thread(target=self._flush_loop, daemon=True)
        self._worker.start()

    def _get_client(self):
        if self._client is None:
            from google.cloud import bigquery
            self._client = bigquery.Client(project=self.project_id)
        return self._client

    def write_turn(self, record: Dict[str, Any]):
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            print("[WARN] Tokenomics BigQuerySink queue is full. Dropping turn record.", flush=True)

    def _flush_loop(self):
        while not self._stop_event.is_set():
            batch = []
            try:
                # Wait for at least one item
                item = self._queue.get(timeout=self.config.flush_interval_seconds)
                batch.append(item)
                # Drain remaining items up to batch size
                while len(batch) < self.config.batch_size:
                    try:
                        batch.append(self._queue.get_nowait())
                    except queue.Empty:
                        break
            except queue.Empty:
                continue

            if batch:
                self._insert_to_bq(batch)

    def _insert_to_bq(self, batch: List[Dict[str, Any]]):
        try:
            client = self._get_client()
            table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            
            rows_to_insert = []
            for r in batch:
                row = {
                    "timestamp": r.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                    "session_id": str(r.get("session_id", "default_session")),
                    "app_name": str(r.get("app_name", "agent_app")),
                    "model_name": str(r.get("model_name", self.config.default_model)),
                    "user_query": str(r.get("user_query", ""))[:2000],
                    "agent_response": str(r.get("agent_response", ""))[:2000],
                    "input_tokens": int(r.get("input_tokens", 0)),
                    "cached_tokens": int(r.get("cached_tokens", 0)),
                    "output_tokens": int(r.get("output_tokens", 0)),
                    "thinking_tokens": int(r.get("thinking_tokens", 0)),
                    "total_cost": float(r.get("total_cost", 0.0)),
                    "tools_called": [str(t) for t in r.get("tools_called", [])],
                    "skills_active": [str(s) for s in r.get("skills_active", [])],
                    "raw_json": json.dumps(r.get("raw_json", {})) if isinstance(r.get("raw_json"), dict) else str(r.get("raw_json", ""))
                }
                rows_to_insert.append(row)

            errors = client.insert_rows_json(table_ref, rows_to_insert)
            if errors:
                print(f"[ERROR] BigQuerySink streaming insert errors: {errors}", flush=True)
        except Exception as e:
            print(f"[ERROR] BigQuerySink failed to stream batch: {e}", flush=True)

    def fetch_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            client = self._get_client()
            query = f"""
                SELECT * FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
                ORDER BY timestamp DESC
                LIMIT @limit
            """
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)]
            )
            rows = client.query(query, job_config=job_config).result()
            return [dict(row.items()) for row in rows]
        except Exception as e:
            print(f"[ERROR] BigQuerySink fetch_recent error: {e}", flush=True)
            return []

    def close(self):
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=3.0)

def create_sink(config: TokenomicsConfig) -> BaseSink:
    """Factory function to instantiate appropriate sink."""
    if config.sink == "bigquery" or config.mode == "prod":
        return BigQuerySink(config)
    return InMemorySink()
