import sys
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Inject parent dir to path to import shared logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_logic
import prompts

from app.agent import DynamicModel, get_agent_config

naive_agent = Agent(
    name="naive_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.NAIVE_INSTRUCTION,
    tools=[shared_logic.search_travel_catalog, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)

bq_plugin = shared_logic.get_bq_analytics_plugin()

app = App(
    root_agent=naive_agent,
    name="naive_app",
    plugins=[bq_plugin] if bq_plugin else None
)

