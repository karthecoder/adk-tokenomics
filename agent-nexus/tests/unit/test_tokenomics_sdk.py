import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from tokenomics import (
    TokenControlTower,
    TokenTracker,
    TokenomicsConfig,
    PricingEngine,
    InMemorySink,
    ADKTokenomicsPlugin,
    track_tokens,
    TokenomicsTestCase,
    FinOpsAggregator,
    assert_cost_under,
    assert_cache_ratio_above,
    assert_token_budget
)

class TestTokenomicsSDK(TokenomicsTestCase):

    def test_pricing_engine_calculations(self):
        engine = PricingEngine()
        res = engine.calculate_turn_cost(
            model_id="publishers/google/models/gemini-3.5-flash",
            input_tokens=10000,
            cached_tokens=40000,
            output_tokens=2000,
            thinking_tokens=1000
        )
        self.assertGreater(res["total_cost"], 0.0)
        self.assertGreater(res["savings_dollars"], 0.0)
        self.assertGreater(res["savings_pct"], 0.0)

    def test_token_tracker_and_assertions(self):
        with self.track_tokens() as tracker:
            tracker.record_turn(
                session_id="s1",
                app_name="caching_app",
                model_name="publishers/google/models/gemini-3.5-flash",
                user_query="Hello",
                agent_response="Hi there!",
                input_tokens=5000,
                cached_tokens=20000,
                output_tokens=500,
                thinking_tokens=100
            )
            self.assertCostLessThan(tracker, max_dollars=0.01)
            self.assertCacheHitRatioGreaterThan(tracker, min_ratio_pct=70.0)
            self.assertTokenBudget(tracker, max_tokens=30000)
            self.assertThinkingTokensWithin(tracker, min_tokens=50, max_tokens=1000)

    def test_finops_aggregator(self):
        records = [
            {
                "model_name": "publishers/google/models/gemini-3.5-flash",
                "app_name": "caching_app",
                "total_cost": 0.01,
                "input_tokens": 1000,
                "cached_tokens": 5000,
                "output_tokens": 200,
                "thinking_tokens": 50
            },
            {
                "model_name": "claude-3-5-sonnet-v2@20241022",
                "app_name": "compaction_app",
                "total_cost": 0.05,
                "input_tokens": 2000,
                "cached_tokens": 0,
                "output_tokens": 400,
                "thinking_tokens": 0
            }
        ]
        agg = FinOpsAggregator.aggregate_records(records)
        self.assertEqual(agg["status"], "success")
        self.assertEqual(agg["kpis"]["total_turns"], 2)
        self.assertEqual(agg["kpis"]["top_provider"], "Anthropic Claude")
        self.assertEqual(len(agg["matrix_rows"]), 2)

    def test_high_level_tower_init(self):
        tower = TokenControlTower(mode="dev")
        self.assertIsNotNone(tower.tracker)
        plugin = tower.create_adk_plugin(app_name="test_bot")
        self.assertEqual(plugin.app_name, "test_bot")

if __name__ == '__main__':
    unittest.main()
