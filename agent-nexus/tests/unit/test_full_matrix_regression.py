import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import app.agent
import shared_logic
import prompts
from app.agent import get_model, DynamicModel, get_agent_config, _fuzzy_get_tool
from google.adk.models.google_llm import Gemini
from google.adk.models.anthropic_llm import Claude
from google.adk.events.event import Event
from google.genai import types

class TestFullMatrixRegression(unittest.TestCase):

    def setUp(self):
        """Load models registry for matrix testing."""
        self.config = shared_logic.load_models_config()
        self.models = self.config.get("models", [])

    def test_model_matrix_resolution(self):
        """Verify model class resolution for every model in registry."""
        for m in self.models:
            m_id = m["id"]
            provider = m["provider"]
            with patch.object(shared_logic, 'get_model_name', return_value=m_id):
                model_inst = get_model()
                if provider == "anthropic":
                    self.assertIsInstance(model_inst, Claude)
                else:
                    self.assertIsInstance(model_inst, Gemini)

    def test_thinking_budget_matrix_conversion(self):
        """Verify all allowed thinking budgets (int & string effort levels) convert cleanly to ThinkingConfig."""
        test_budgets = [0, 1024, 2048, 4096, -1, "off", "low", "medium", "high", "OFF", "HIGH"]
        for b in test_budgets:
            with patch.object(shared_logic, 'get_thinking_budget', return_value=b):
                cfg = get_agent_config()
                self.assertIsNotNone(cfg.thinking_config)
                self.assertIsInstance(cfg.thinking_config.thinking_budget, int)

    def test_fuzzy_tool_resolution_matrix(self):
        """Verify hallucinated tool names and namespace prefixes resolve to valid registered tools."""
        tools_dict = {
            "google_search": shared_logic.google_search,
            "google_news_search": shared_logic.google_news_search,
            "web_search": shared_logic.web_search,
            "get_weather": shared_logic.get_weather,
            "get_current_time": shared_logic.get_current_time
        }

        test_cases = [
            ("google_search", "google_search"),
            ("default me:default_api:google_news_search", "google_news_search"),
            ("default_api:google_search", "google_search"),
            ("hallucinated_web_search_query", "google_search"),
            ("default_api:get_weather", "get_weather")
        ]

        for input_name, expected_name in test_cases:
            call_obj = MagicMock()
            call_obj.name = input_name
            tool_func = _fuzzy_get_tool(call_obj, tools_dict)
            self.assertEqual(call_obj.name, expected_name)
            self.assertIsNotNone(tool_func)

    def test_prune_thoughts_history_hygiene(self):
        """Verify history pruning never leaves empty parts list when pruning thought-only model turns."""
        mock_event = MagicMock()
        mock_event.role = "model"
        
        # 1. Turn with thought part and text part
        thought_part = MagicMock()
        thought_part.thought = True
        text_part = types.Part.from_text(text="Hello world")
        text_part.thought = False
        
        mock_event.content.parts = [thought_part, text_part]
        mock_context = MagicMock()
        mock_context.session.events = [mock_event]

        shared_logic.prune_thoughts_from_history(mock_context)
        self.assertEqual(len(mock_event.content.parts), 1)
        self.assertEqual(mock_event.content.parts[0].text, "Hello world")

        # 2. Turn with ONLY thought part (all pruned)
        only_thought_part = MagicMock()
        only_thought_part.thought = True
        mock_event_2 = MagicMock()
        mock_event_2.role = "model"
        mock_event_2.content.parts = [only_thought_part]
        mock_context_2 = MagicMock()
        mock_context_2.session.events = [mock_event_2]

        shared_logic.prune_thoughts_from_history(mock_context_2)
        # Must retain placeholder text part to avoid empty parts error
        self.assertEqual(len(mock_event_2.content.parts), 1)
        self.assertEqual(mock_event_2.content.parts[0].text, "[Thinking completed]")

    def test_anthropic_system_instruction_formatter(self):
        """Verify string system instructions convert to Anthropic list of text blocks."""
        sys_str = "You are a travel assistant."
        formatted = app.agent._format_anthropic_system(sys_str)
        self.assertIsInstance(formatted, list)
        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0]["type"], "text")
        self.assertEqual(formatted[0]["text"], sys_str)

    def test_scenario_apps_matrix(self):
        """Verify all 4 scenario apps (naive, caching, compaction, skills) have valid root agents & tools."""
        apps = [
            ("naive_app", app.agent.naive_app),
            ("caching_app", app.agent.caching_app),
            ("compaction_app", app.agent.compaction_app),
            ("skills_app", app.agent.skills_app)
        ]
        for name, a in apps:
            self.assertEqual(a.name, name)
            self.assertIsNotNone(a.root_agent)
            self.assertGreaterEqual(len(a.root_agent.tools), 3)

if __name__ == '__main__':
    unittest.main()
