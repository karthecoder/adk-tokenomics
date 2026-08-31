"""
Tokenomics SDK - Rate Card & Pricing Engine
Calculates granular turn costs and optimization ROI across all LLM vendors.
"""

from typing import Dict, Any, Optional
from tokenomics.core.config import TokenomicsConfig

class PricingEngine:
    def __init__(self, config: Optional[TokenomicsConfig] = None):
        self.config = config or TokenomicsConfig()
        self._load_rates()

    def _load_rates(self):
        models_data = self.config.get_models_config()
        self.pricing_table = {}
        for m in models_data.get("models", []):
            m_id = m.get("id")
            p = m.get("pricing", {})
            self.pricing_table[m_id] = {
                "name": m.get("name", m_id),
                "provider": m.get("provider", "google"),
                "input": p.get("input_per_million", 0.30),
                "cached": p.get("cached_per_million", 0.075),
                "output": p.get("output_per_million", 1.20)
            }

    def get_rate(self, model_id: str) -> Dict[str, Any]:
        """Returns pricing rate card for a given model ID."""
        if model_id in self.pricing_table:
            return self.pricing_table[model_id]
        
        # Fallback by substring match
        mid_lower = str(model_id).lower()
        if "pro" in mid_lower:
            return {"name": "Pro Tier", "provider": "google", "input": 1.25, "cached": 0.3125, "output": 5.00}
        if "claude" in mid_lower or "sonnet" in mid_lower:
            return {"name": "Claude Sonnet", "provider": "anthropic", "input": 3.00, "cached": 0.30, "output": 15.00}
        if "gpt" in mid_lower:
            return {"name": "GPT-4o", "provider": "openai", "input": 2.50, "cached": 1.25, "output": 10.00}
        
        # Default Flash rate
        return {"name": "Gemini Flash Default", "provider": "google", "input": 0.30, "cached": 0.075, "output": 1.20}

    def calculate_turn_cost(
        self,
        model_id: str,
        input_tokens: int,
        cached_tokens: int,
        output_tokens: int,
        thinking_tokens: int = 0
    ) -> Dict[str, float]:
        """Calculates precise dollar cost for a turn."""
        rates = self.get_rate(model_id)
        
        input_cost = (input_tokens / 1_000_000.0) * rates["input"]
        cached_cost = (cached_tokens / 1_000_000.0) * rates["cached"]
        # Output + thinking tokens billed at output rate
        total_gen_tokens = output_tokens + thinking_tokens
        output_cost = (total_gen_tokens / 1_000_000.0) * rates["output"]
        
        total_cost = input_cost + cached_cost + output_cost
        
        # Hypothetical naive uncached cost
        naive_hypothetical = ((input_tokens + cached_tokens) / 1_000_000.0) * rates["input"] + output_cost
        savings_dollars = max(0.0, naive_hypothetical - total_cost)
        savings_pct = (savings_dollars / naive_hypothetical * 100.0) if naive_hypothetical > 0 else 0.0

        return {
            "input_cost": input_cost,
            "cached_cost": cached_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "hypothetical_uncached_cost": naive_hypothetical,
            "savings_dollars": savings_dollars,
            "savings_pct": savings_pct,
            "rates_used": rates
        }
