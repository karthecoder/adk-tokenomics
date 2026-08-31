"""
Tokenomics SDK - FinOps Matrix Aggregator & Reporting Engine
"""

from typing import Dict, Any, List

class FinOpsAggregator:
    """Aggregates raw turn records into multi-dimensional executive FinOps summaries."""

    @staticmethod
    def classify_provider(model_name: str) -> str:
        m = str(model_name).lower()
        if "claude" in m or "anthropic" in m or "sonnet" in m:
            return "Anthropic Claude"
        elif "gpt" in m or "openai" in m or "o1" in m or "o3" in m:
            return "OpenAI"
        elif "gemini" in m or "google" in m or "flash" in m or "pro" in m:
            return "Google Gemini"
        return "Other"

    @classmethod
    def aggregate_records(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_spend = 0.0
        total_tokens = 0
        total_input = 0
        total_cached = 0
        total_output = 0
        total_thinking = 0
        total_turns = len(records)

        provider_map = {
            "Google Gemini": {"spend": 0.0, "turns": 0, "input": 0, "cached": 0, "output": 0, "thinking": 0},
            "Anthropic Claude": {"spend": 0.0, "turns": 0, "input": 0, "cached": 0, "output": 0, "thinking": 0},
            "OpenAI": {"spend": 0.0, "turns": 0, "input": 0, "cached": 0, "output": 0, "thinking": 0},
            "Other": {"spend": 0.0, "turns": 0, "input": 0, "cached": 0, "output": 0, "thinking": 0}
        }

        matrix_groups: Dict[tuple, Dict[str, Any]] = {}

        for r in records:
            cost = float(r.get("total_cost", 0.0))
            in_tok = int(r.get("input_tokens", 0))
            cache_tok = int(r.get("cached_tokens", 0))
            out_tok = int(r.get("output_tokens", 0))
            think_tok = int(r.get("thinking_tokens", 0))
            tok_sum = in_tok + cache_tok + out_tok + think_tok
            
            total_spend += cost
            total_tokens += tok_sum
            total_input += in_tok
            total_cached += cache_tok
            total_output += out_tok
            total_thinking += think_tok

            prov = cls.classify_provider(r.get("model_name", ""))
            provider_map[prov]["spend"] += cost
            provider_map[prov]["turns"] += 1
            provider_map[prov]["input"] += in_tok
            provider_map[prov]["cached"] += cache_tok
            provider_map[prov]["output"] += out_tok
            provider_map[prov]["thinking"] += think_tok

            # Matrix grouping (provider, model, app)
            key = (prov, str(r.get("model_name", "unknown")), str(r.get("app_name", "app")))
            if key not in matrix_groups:
                matrix_groups[key] = {
                    "provider": prov,
                    "model_name": key[1],
                    "app_name": key[2],
                    "turns": 0,
                    "input_tokens": 0,
                    "cached_tokens": 0,
                    "output_tokens": 0,
                    "thinking_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            g = matrix_groups[key]
            g["turns"] += 1
            g["input_tokens"] += in_tok
            g["cached_tokens"] += cache_tok
            g["output_tokens"] += out_tok
            g["thinking_tokens"] += think_tok
            g["total_tokens"] += tok_sum
            g["total_cost"] += cost

        # Top provider calculation
        top_provider = "None"
        top_spend = 0.0
        for p, data in provider_map.items():
            if data["spend"] > top_spend:
                top_spend = data["spend"]
                top_provider = p

        top_share = (top_spend / total_spend * 100.0) if total_spend > 0 else 0.0
        blended_cost = (total_spend / total_tokens * 1_000_000.0) if total_tokens > 0 else 0.0
        
        # Optimization savings calculation ($0.225 / 1M cached tokens on Gemini Flash baseline)
        savings_dollars = (total_cached / 1_000_000.0) * (0.30 - 0.075)
        hypothetical_baseline = total_spend + savings_dollars
        savings_pct = (savings_dollars / hypothetical_baseline * 100.0) if hypothetical_baseline > 0 else 0.0

        # Build matrix rows with spend share
        matrix_rows = []
        for g in sorted(matrix_groups.values(), key=lambda x: x["total_cost"], reverse=True):
            share = (g["total_cost"] / total_spend * 100.0) if total_spend > 0 else 0.0
            g["spend_share_pct"] = round(share, 1)
            g["total_cost"] = round(g["total_cost"], 5)
            matrix_rows.append(g)

        return {
            "status": "success",
            "kpis": {
                "total_spend": round(total_spend, 5),
                "total_tokens": total_tokens,
                "total_input": total_input,
                "total_cached": total_cached,
                "total_output": total_output,
                "total_thinking": total_thinking,
                "total_turns": total_turns,
                "blended_cost_per_1m": round(blended_cost, 3),
                "top_provider": top_provider,
                "top_provider_share": round(top_share, 1),
                "optimization_savings_dollars": round(savings_dollars, 4),
                "optimization_savings_pct": round(savings_pct, 1)
            },
            "provider_breakdown": provider_map,
            "matrix_rows": matrix_rows
        }
