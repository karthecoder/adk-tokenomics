"""
Tokenomics SDK - Python Decorator for Custom Functions & Pipelines
"""

import functools
import time
from typing import Callable, Any, Optional
from tokenomics.core.tracker import TokenTracker

_GLOBAL_TRACKER = TokenTracker()

def track_tokens(
    app_name: str = "custom_agent",
    model_name: str = "publishers/google/models/gemini-3.5-flash",
    tracker: Optional[TokenTracker] = None
):
    """
    Decorator to wrap any LLM invocation function and automatically track tokenomics.
    
    Usage:
        @track_tokens(app_name="rag_search", model_name="publishers/google/models/gemini-3.5-flash")
        def ask_agent(prompt: str) -> str:
            # Custom LLM call
            return response
    """
    active_tracker = tracker or _GLOBAL_TRACKER

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # If function returns an object with usage metadata or tuple (response, usage)
            input_tokens = 0
            cached_tokens = 0
            output_tokens = 0
            thinking_tokens = 0

            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                usage = result[1]
                input_tokens = usage.get("input_tokens", 0)
                cached_tokens = usage.get("cached_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                thinking_tokens = usage.get("thinking_tokens", 0)
                resp_text = str(result[0])
            else:
                resp_text = str(result)

            active_tracker.record_turn(
                session_id="decorated_session",
                app_name=app_name,
                model_name=model_name,
                user_query=str(args[0]) if len(args) > 0 else "function_call",
                agent_response=resp_text[:1000],
                input_tokens=input_tokens,
                cached_tokens=cached_tokens,
                output_tokens=output_tokens,
                thinking_tokens=thinking_tokens
            )
            return result
        return wrapper
    return decorator
