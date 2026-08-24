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
from google.genai import types

class TestGeminiFlashRegression(unittest.TestCase):

    def setUp(self):
        self.gemini_models = [
            "publishers/google/models/gemini-3.5-flash",
            "publishers/google/models/gemini-3.6-flash",
            "publishers/google/models/gemini-3.7-flash"
        ]

    def test_gemini_model_instantiation(self):
        """Test resolution and instantiation for Gemini 3.5, 3.6, and 3.7 Flash."""
        for m_name in self.gemini_models:
            with patch.object(shared_logic, 'get_model_name', return_value=m_name):
                model = get_model()
                self.assertIsInstance(model, Gemini)
                self.assertEqual(model.model, m_name)

    def test_gemini_thinking_budget_conversion(self):
        """Test integer & string thinking budget conversions into valid types.ThinkingConfig."""
        budgets_to_test = [
            (0, 0),
            (1024, 1024),
            (2048, 2048),
            (4096, 4096),
            (-1, -1),
            ("off", 0),
            ("low", 1024),
            ("medium", 2048),
            ("high", 4096),
            ("dynamic", -1)
        ]
        for input_b, expected_b in budgets_to_test:
            with patch.object(shared_logic, 'get_thinking_budget', return_value=input_b):
                cfg = get_agent_config()
                self.assertIsNotNone(cfg.thinking_config)
                self.assertEqual(cfg.thinking_config.thinking_budget, expected_b)

    def test_gemini_max_output_tokens(self):
        """Test max output token bounds configuration across Gemini models."""
        for token_limit in [1024, 2048, 4096, 8192, 16384]:
            with patch.object(shared_logic, 'get_max_output_tokens', return_value=token_limit):
                cfg = get_agent_config()
                self.assertEqual(cfg.max_output_tokens, token_limit)

    def test_gemini_fuzzy_tool_resolution(self):
        """Test fuzzy tool resolution for Gemini function calls."""
        tools_dict = {
            "google_search": shared_logic.google_search,
            "get_weather": shared_logic.get_weather,
            "get_current_time": shared_logic.get_current_time
        }

        test_calls = [
            ("default_api:google_search", "google_search"),
            ("default me:default_api:google_news_search", "google_search"),
            ("hallucinated_web_search_query", "google_search"),
            ("default_api:get_weather", "get_weather")
        ]

        for raw_name, expected_name in test_calls:
            call_obj = MagicMock()
            call_obj.name = raw_name
            tool_func = _fuzzy_get_tool(call_obj, tools_dict)
            self.assertEqual(call_obj.name, expected_name)
            self.assertIsNotNone(tool_func)

    def test_gemini_thought_pruning_hygiene(self):
        """Test thought pruning for Gemini model responses retains non-empty parts."""
        # 1. Mixed turn
        thought_part = MagicMock()
        thought_part.thought = True
        text_part = types.Part.from_text(text="Gemini response text")
        text_part.thought = False

        mock_event = MagicMock()
        mock_event.role = "model"
        mock_event.content.parts = [thought_part, text_part]

        mock_context = MagicMock()
        mock_context.session.events = [mock_event]

        shared_logic.prune_thoughts_from_history(mock_context)
        self.assertEqual(len(mock_event.content.parts), 1)
        self.assertEqual(mock_event.content.parts[0].text, "Gemini response text")

        # 2. Thought-only turn
        only_thought = MagicMock()
        only_thought.thought = True
        mock_event_2 = MagicMock()
        mock_event_2.role = "model"
        mock_event_2.content.parts = [only_thought]

        mock_context_2 = MagicMock()
        mock_context_2.session.events = [mock_event_2]

        shared_logic.prune_thoughts_from_history(mock_context_2)
        self.assertEqual(len(mock_event_2.content.parts), 1)
        self.assertEqual(mock_event_2.content.parts[0].text, "[Thinking completed]")

    def test_gemini_pricing_rate_cards(self):
        """Test pricing rate card lookup for all 3 Gemini Flash models."""
        pricing = shared_logic.get_pricing()
        for m_name in self.gemini_models:
            self.assertIn(m_name, pricing)
            rates = pricing[m_name]
            self.assertIn("input", rates)
            self.assertIn("cached", rates)
            self.assertIn("output", rates)

    def test_gemini_scenario_apps_integration(self):
        """Test that all scenario apps correctly bind Gemini models."""
        apps = [app.agent.naive_app, app.agent.caching_app, app.agent.compaction_app, app.agent.skills_app]
        for a in apps:
            self.assertIsNotNone(a.root_agent)
            self.assertIsInstance(a.root_agent.model, DynamicModel)

if __name__ == '__main__':
    unittest.main()
