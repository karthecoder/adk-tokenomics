import sys
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.agents.context_cache_config import ContextCacheConfig

# Inject parent dir to path to import shared logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_logic
import prompts

from app.agent import DynamicModel, get_agent_config

caching_agent = Agent(
    name="caching_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.CACHING_INSTRUCTION,
    tools=[shared_logic.get_weather, shared_logic.get_current_time, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)

app = App(
    root_agent=caching_agent,
    name="caching_app",
    context_cache_config=ContextCacheConfig(min_tokens=1024, ttl_seconds=300)
)
