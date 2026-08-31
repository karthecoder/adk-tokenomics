"""
Tokenomics SDK - Testing & CI/CD Regression Assertions
Enables teams to enforce financial token budgets and cache optimization gates in CI/CD.
"""

from typing import Union
from tokenomics.core.tracker import TokenTracker

def assert_cost_under(tracker: TokenTracker, max_dollars: float, msg: str = ""):
    """Asserts that total accumulated dollar cost is strictly under the specified budget threshold."""
    summary = tracker.get_summary()
    actual_cost = summary["total_cost"]
    err_msg = msg or f"Cost budget exceeded! Expected cost <= ${max_dollars:.5f}, but was ${actual_cost:.5f}"
    assert actual_cost <= max_dollars, err_msg

def assert_cache_ratio_above(tracker: TokenTracker, min_ratio_pct: float, msg: str = ""):
    """Asserts that context caching read ratio meets or exceeds the required efficiency percentage."""
    summary = tracker.get_summary()
    actual_ratio = summary["cache_read_ratio_pct"]
    err_msg = msg or f"Context caching efficiency too low! Expected >= {min_ratio_pct:.1f}%, but was {actual_ratio:.1f}%"
    assert actual_ratio >= min_ratio_pct, err_msg

def assert_token_budget(tracker: TokenTracker, max_tokens: int, msg: str = ""):
    """Asserts that total tokens consumed is within the allocated token budget."""
    summary = tracker.get_summary()
    actual_tokens = summary["total_tokens"]
    err_msg = msg or f"Token budget exceeded! Expected total tokens <= {max_tokens}, but was {actual_tokens}"
    assert actual_tokens <= max_tokens, err_msg

def assert_thinking_budget(tracker: TokenTracker, min_tokens: int = 0, max_tokens: int = 8192, msg: str = ""):
    """Asserts that reasoning/thinking tokens fall within expected bounds."""
    summary = tracker.get_summary()
    actual_thinking = summary["thinking_tokens"]
    err_msg = msg or f"Thinking tokens out of bounds! Expected between {min_tokens} and {max_tokens}, but was {actual_thinking}"
    assert min_tokens <= actual_thinking <= max_tokens, err_msg
