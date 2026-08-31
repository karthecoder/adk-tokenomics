"""
Tokenomics SDK - Unittest Base Class for Automated Agent Token Regression Testing
"""

import unittest
from contextlib import contextmanager
from tokenomics.core.config import TokenomicsConfig
from tokenomics.core.sinks import InMemorySink
from tokenomics.core.tracker import TokenTracker
from tokenomics.testing.assertions import (
    assert_cost_under,
    assert_cache_ratio_above,
    assert_token_budget,
    assert_thinking_budget
)

class TokenomicsTestCase(unittest.TestCase):
    """
    Base test case equipped with isolated TokenTracker and assertion helpers.
    
    Usage:
        class TestMyAgent(TokenomicsTestCase):
            def test_summary_workflow(self):
                with self.track_tokens() as tracker:
                    # Run agent turn
                    tracker.record_turn(...)
                    self.assertCostLessThan(tracker, max_dollars=0.005)
                    self.assertCacheHitRatioGreaterThan(tracker, min_ratio=50.0)
    """
    def setUp(self):
        super().setUp()
        self.config = TokenomicsConfig(mode="test", sink="memory")
        self.sink = InMemorySink()
        self.tracker = TokenTracker(config=self.config, sink=self.sink)

    @contextmanager
    def track_tokens(self):
        """Context manager to measure token consumption inside a test block."""
        scoped_tracker = TokenTracker(config=self.config, sink=self.sink)
        try:
            yield scoped_tracker
        finally:
            pass

    def assertCostLessThan(self, tracker: TokenTracker, max_dollars: float, msg: str = ""):
        assert_cost_under(tracker, max_dollars, msg)

    def assertCacheHitRatioGreaterThan(self, tracker: TokenTracker, min_ratio_pct: float, msg: str = ""):
        assert_cache_ratio_above(tracker, min_ratio_pct, msg)

    def assertTokenBudget(self, tracker: TokenTracker, max_tokens: int, msg: str = ""):
        assert_token_budget(tracker, max_tokens, msg)

    def assertThinkingTokensWithin(self, tracker: TokenTracker, min_tokens: int = 0, max_tokens: int = 8192, msg: str = ""):
        assert_thinking_budget(tracker, min_tokens, max_tokens, msg)
