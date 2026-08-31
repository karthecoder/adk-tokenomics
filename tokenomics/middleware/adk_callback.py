"""
Tokenomics SDK - Google ADK Plugin & Callbacks
Plug-and-play middleware that automatically captures ADK turn telemetry without manual instrumentation.
"""

from typing import Optional, Dict, Any, List
from tokenomics.core.tracker import TokenTracker

class ADKTokenomicsPlugin:
    """
    Drop-in Google ADK Plugin for automated tokenomics telemetry.
    
    Usage:
        from tokenomics.middleware.adk_callback import ADKTokenomicsPlugin
        
        plugin = ADKTokenomicsPlugin(app_name="customer_agent")
        # Attach to ADK Agent or Runner
    """
    def __init__(self, tracker: Optional[TokenTracker] = None, app_name: str = "adk_agent"):
        self.tracker = tracker or TokenTracker()
        self.app_name = app_name

    def on_event(self, event: Any, session_id: str = "default_session", user_query: str = "") -> Optional[Dict[str, Any]]:
        """Extracts token metrics from ADK event object."""
        usage = getattr(event, "usage_metadata", None)
        if not usage:
            return None

        # Extract standard GenAI token attributes
        prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
        cached_tokens = getattr(usage, "cached_content_token_count", 0) or 0
        candidates_tokens = getattr(usage, "candidates_token_count", 0) or 0
        thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0

        # Fresh input is prompt minus cached
        fresh_input = max(0, prompt_tokens - cached_tokens)
        
        model_name = getattr(event, "model_version", None) or getattr(event, "model", "publishers/google/models/gemini-3.5-flash")
        
        # Extract response text if available
        response_text = ""
        candidates = getattr(event, "candidates", None)
        if candidates and len(candidates) > 0:
            content = getattr(candidates[0], "content", None)
            if content and hasattr(content, "parts"):
                parts_text = [getattr(p, "text", "") for p in content.parts if hasattr(p, "text")]
                response_text = " ".join(filter(None, parts_text))

        return self.tracker.record_turn(
            session_id=session_id,
            app_name=self.app_name,
            model_name=str(model_name),
            user_query=user_query,
            agent_response=response_text[:1000],
            input_tokens=fresh_input,
            cached_tokens=cached_tokens,
            output_tokens=candidates_tokens,
            thinking_tokens=thinking_tokens,
            raw_json={"usage": str(usage)}
        )
