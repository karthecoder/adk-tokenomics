"""
Tokenomics SDK - Core Configuration Manager
Supports Prototyping, Development, Testing, and Production environments.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

DEFAULT_MODELS_CONFIG = {
    "models": [
        {
            "id": "publishers/google/models/gemini-3.5-flash",
            "name": "Gemini 3.5 Flash",
            "provider": "google",
            "pricing": {
                "input_per_million": 0.30,
                "cached_per_million": 0.075,
                "output_per_million": 1.20
            },
            "thinking_budget": 0,
            "max_output_tokens": 8192
        },
        {
            "id": "publishers/google/models/gemini-3.5-pro",
            "name": "Gemini 3.5 Pro",
            "provider": "google",
            "pricing": {
                "input_per_million": 1.25,
                "cached_per_million": 0.3125,
                "output_per_million": 5.00
            },
            "thinking_budget": 0,
            "max_output_tokens": 8192
        },
        {
            "id": "publishers/google/models/gemini-3.7-flash",
            "name": "Gemini 3.7 Flash",
            "provider": "google",
            "pricing": {
                "input_per_million": 0.30,
                "cached_per_million": 0.075,
                "output_per_million": 1.20
            },
            "thinking_budget": 4096,
            "max_output_tokens": 8192
        },
        {
            "id": "publishers/google/models/gemini-3.7-pro",
            "name": "Gemini 3.7 Pro",
            "provider": "google",
            "pricing": {
                "input_per_million": 1.25,
                "cached_per_million": 0.3125,
                "output_per_million": 5.00
            },
            "thinking_budget": 4096,
            "max_output_tokens": 8192
        },
        {
            "id": "claude-3-5-sonnet-v2@20241022",
            "name": "Claude 3.5 Sonnet v2",
            "provider": "anthropic",
            "pricing": {
                "input_per_million": 3.00,
                "cached_per_million": 0.30,
                "output_per_million": 15.00
            },
            "thinking_budget": 0,
            "max_output_tokens": 8192
        },
        {
            "id": "gpt-4o",
            "name": "OpenAI GPT-4o",
            "provider": "openai",
            "pricing": {
                "input_per_million": 2.50,
                "cached_per_million": 1.25,
                "output_per_million": 10.00
            },
            "thinking_budget": 0,
            "max_output_tokens": 4096
        }
    ]
}

@dataclass
class TokenomicsConfig:
    """Central configuration for Tokenomics SDK."""
    mode: str = "dev"  # "prototype", "dev", "test", "prod"
    sink: str = "memory"  # "memory", "sqlite", "duckdb", "bigquery"
    project_id: Optional[str] = None
    dataset_id: str = "bq_adk_ds"
    table_id: str = "token_consumption_logs"
    default_model: str = "publishers/google/models/gemini-3.5-flash"
    models_config_path: Optional[str] = None
    async_streaming: bool = True
    batch_size: int = 10
    flush_interval_seconds: float = 2.0
    custom_pricing: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.project_id:
            self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("GCP_PROJECT", "vertexai-demo-ltfpzhaw"))
        
        env_mode = os.environ.get("TOKENOMICS_MODE")
        if env_mode:
            self.mode = env_mode.lower()
            
        env_sink = os.environ.get("TOKENOMICS_SINK")
        if env_sink:
            self.sink = env_sink.lower()

    def get_models_config(self) -> Dict[str, Any]:
        """Loads models configuration from file or default."""
        if self.models_config_path and os.path.exists(self.models_config_path):
            try:
                with open(self.models_config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_MODELS_CONFIG
