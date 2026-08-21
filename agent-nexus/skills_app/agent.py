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

skills_catalog = shared_logic.discover_skills()

skills_agent = Agent(
    name="skills_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.SKILLS_INSTRUCTION_TEMPLATE.format(skills_catalog=skills_catalog),
    tools=[shared_logic.get_weather, shared_logic.get_current_time, shared_logic.activate_skill, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)

app = App(
    root_agent=skills_agent,
    name="skills_app"
)
