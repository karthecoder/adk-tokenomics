"""
Tokenomics SDK - TokenControlTower Main Hub
High-level plug-and-play interface for connecting Tokenomics to any AI Agent lifecycle.
"""

import os
import sys
import subprocess
from typing import Optional, Any, Dict
from tokenomics.core.config import TokenomicsConfig
from tokenomics.core.tracker import TokenTracker
from tokenomics.core.sinks import create_sink, BaseSink
from tokenomics.middleware.adk_callback import ADKTokenomicsPlugin
from tokenomics.finops.bq_schema import provision_bigquery_table

class TokenControlTower:
    """
    Main entrypoint for Tokenomics SDK.
    
    Quickstart:
        tower = TokenControlTower(mode="dev")
        tower.track_turn(...)
        tower.launch_ui(port=8080)
    """
    def __init__(
        self,
        mode: str = "dev",
        sink: Optional[str] = None,
        project_id: Optional[str] = None,
        dataset_id: str = "bq_adk_ds",
        table_id: str = "token_consumption_logs",
        default_model: str = "publishers/google/models/gemini-3.5-flash"
    ):
        self.config = TokenomicsConfig(
            mode=mode,
            sink=sink or ("bigquery" if mode == "prod" else "memory"),
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            default_model=default_model
        )
        self.sink = create_sink(self.config)
        self.tracker = TokenTracker(config=self.config, sink=self.sink)

    def create_adk_plugin(self, app_name: str = "customer_agent") -> ADKTokenomicsPlugin:
        """Returns a drop-in Google ADK plugin for this control tower."""
        return ADKTokenomicsPlugin(tracker=self.tracker, app_name=app_name)

    def track_turn(self, **kwargs) -> Dict[str, Any]:
        """Convenience method to record a turn directly."""
        return self.tracker.record_turn(**kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """Returns live session metrics summary."""
        return self.tracker.get_summary()

    def provision_cloud_infra(self) -> bool:
        """Provisions production BigQuery partitioned dataset and table."""
        if not self.config.project_id:
            print("[ERROR] GOOGLE_CLOUD_PROJECT must be set to provision BigQuery table.", flush=True)
            return False
        return provision_bigquery_table(
            project_id=self.config.project_id,
            dataset_id=self.config.dataset_id,
            table_id=self.config.table_id
        )

    def launch_ui(self, port: int = 8080, host: str = "0.0.0.0"):
        """Launches the interactive Token Control Tower Web UI locally."""
        server_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")
        if os.path.exists(server_script):
            print(f"🚀 Starting Token Control Tower UI on http://{host}:{port} ...", flush=True)
            subprocess.run([sys.executable, server_script, "--port", str(port)])
        else:
            print(f"[ERROR] server.py not found at {server_script}", flush=True)
