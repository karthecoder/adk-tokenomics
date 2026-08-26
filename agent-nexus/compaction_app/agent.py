import sys
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.apps.app import EventsCompactionConfig

# Inject parent dir to path to import shared logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_logic
import prompts

from app.agent import DynamicModel, get_agent_config

compaction_agent = Agent(
    name="compaction_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.COMPACTION_INSTRUCTION,
    tools=[shared_logic.search_travel_catalog, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)

app = App(
    root_agent=compaction_agent,
    name="compaction_app",
    events_compaction_config=EventsCompactionConfig(compaction_interval=4, overlap_size=1)
)
