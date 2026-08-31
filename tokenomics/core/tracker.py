"""
Tokenomics SDK - Core TokenTracker Engine
Extracts token usage, computes costs, calculates cache ratios, and dispatches turns to sinks.
"""

import time
import datetime
from typing import Dict, Any, Optional, List
from tokenomics.core.config import TokenomicsConfig
from tokenomics.core.pricing import PricingEngine
from tokenomics.core.sinks import BaseSink, create_sink

class TokenTracker:
    def __init__(self, config: Optional[TokenomicsConfig] = None, sink: Optional[BaseSink] = None):
        self.config = config or TokenomicsConfig()
        self.pricing = PricingEngine(self.config)
        self.sink = sink or create_sink(self.config)
        
        # Session metrics
        self.total_input_tokens = 0
        self.total_cached_tokens = 0
        self.total_output_tokens = 0
        self.total_thinking_tokens = 0
        self.total_cost = 0.0
        self.total_turns = 0
        self.turns_history: List[Dict[str, Any]] = []

    def record_turn(
        self,
        session_id: str,
        app_name: str,
        model_name: str,
        user_query: str,
        agent_response: str,
        input_tokens: int,
        cached_tokens: int,
        output_tokens: int,
        thinking_tokens: int = 0,
        tools_called: Optional[List[str]] = None,
        skills_active: Optional[List[str]] = None,
        raw_json: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Records a single LLM turn and persists to configured telemetry sink."""
        cost_info = self.pricing.calculate_turn_cost(
            model_id=model_name,
            input_tokens=input_tokens,
            cached_tokens=cached_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens
        )

        turn_record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "session_id": session_id,
            "app_name": app_name,
            "model_name": model_name,
            "user_query": user_query,
            "agent_response": agent_response,
            "input_tokens": input_tokens,
            "cached_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "total_tokens": input_tokens + cached_tokens + output_tokens + thinking_tokens,
            "total_cost": cost_info["total_cost"],
            "cost_breakdown": cost_info,
            "tools_called": tools_called or [],
            "skills_active": skills_active or [],
            "raw_json": raw_json or {}
        }

        # Update in-memory session totals
        self.total_input_tokens += input_tokens
        self.total_cached_tokens += cached_tokens
        self.total_output_tokens += output_tokens
        self.total_thinking_tokens += thinking_tokens
        self.total_cost += cost_info["total_cost"]
        self.total_turns += 1
        self.turns_history.append(turn_record)

        # Dispatch to sink
        self.sink.write_turn(turn_record)
        return turn_record

    def get_summary(self) -> Dict[str, Any]:
        """Returns session summary metrics."""
        total_in = self.total_input_tokens + self.total_cached_tokens
        cache_ratio = (self.total_cached_tokens / total_in * 100.0) if total_in > 0 else 0.0
        total_toks = self.total_input_tokens + self.total_cached_tokens + self.total_output_tokens + self.total_thinking_tokens
        blended_cost = (self.total_cost / total_toks * 1_000_000.0) if total_toks > 0 else 0.0

        return {
            "total_turns": self.total_turns,
            "total_cost": self.total_cost,
            "total_tokens": total_toks,
            "input_tokens": self.total_input_tokens,
            "cached_tokens": self.total_cached_tokens,
            "output_tokens": self.total_output_tokens,
            "thinking_tokens": self.total_thinking_tokens,
            "cache_read_ratio_pct": cache_ratio,
            "blended_cost_per_1m": blended_cost
        }
