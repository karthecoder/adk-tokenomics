import sys
import os
import unittest
import asyncio
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import app.agent
import shared_logic
from app.agent import get_model, DynamicModel, _fuzzy_get_tool, _format_anthropic_system
import google.adk.models.anthropic_llm as anthropic_llm_module
from google.adk.models.anthropic_llm import Claude
from google.adk.models.llm_request import LlmRequest
from google.genai import types

class TestClaudeRegression(unittest.TestCase):

    def test_claude_instantiation(self):
        """Test get_model resolves to Claude instance when DEMO_MODEL_NAME is set to claude-sonnet-5."""
        with patch.object(shared_logic, 'get_model_name', return_value="claude-sonnet-5"):
            model = get_model()
            self.assertIsInstance(model, Claude)
            self.assertEqual(model.model, "claude-sonnet-5")

    def test_claude_thinking_param_builder(self):
        """Test Anthropic thinking parameter builder for disabled (0) vs adaptive (positive)."""
        # Disabled
        cfg_0 = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
        param_0 = anthropic_llm_module._build_anthropic_thinking_param(cfg_0)
        self.assertEqual(param_0["type"], "disabled")

        # Adaptive
        cfg_4096 = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=4096))
        param_4096 = anthropic_llm_module._build_anthropic_thinking_param(cfg_4096)
        self.assertEqual(param_4096["type"], "adaptive")

    def test_claude_system_instruction_formatter(self):
        """Test Anthropic system instruction string and object formatters."""
        # String input
        sys_str = "You are a travel planning assistant."
        res_str = _format_anthropic_system(sys_str)
        self.assertEqual(res_str, [{"type": "text", "text": sys_str}])

        # List input
        sys_list = [{"type": "text", "text": sys_str}]
        res_list = _format_anthropic_system(sys_list)
        self.assertEqual(res_list, sys_list)

        # None input returns NOT_GIVEN
        self.assertEqual(_format_anthropic_system(None), anthropic_llm_module.NOT_GIVEN)

    def test_claude_usage_parsing_with_thinking_tokens(self):
        """Test Anthropic usage metadata parsing including reasoning/thinking token counts."""
        mock_usage = MagicMock()
        mock_usage.input_tokens = 1500
        mock_usage.output_tokens = 2400

        mock_details = MagicMock()
        mock_details.thinking_tokens = 1200
        mock_usage.output_tokens_details = mock_details

        mock_msg = MagicMock()
        mock_msg.content = []
        mock_msg.usage = mock_usage

        resp = app.agent._patched_message_to_generate_content_response(mock_msg)
        usage = resp.usage_metadata

        self.assertEqual(usage.prompt_token_count, 1500)
        self.assertEqual(usage.candidates_token_count, 2400)
        self.assertEqual(usage.thoughts_token_count, 1200)
        self.assertEqual(usage.total_token_count, 3900)

    def test_claude_fuzzy_tool_resolution(self):
        """Test fuzzy tool resolution for Anthropic function calls with hallucinated namespace prefixes."""
        tools_dict = {
            "google_search": shared_logic.google_search,
            "get_weather": shared_logic.get_weather,
            "get_current_time": shared_logic.get_current_time
        }

        call_obj = MagicMock()
        call_obj.name = "default me:default_api:google_news_search"
        
        tool_func = _fuzzy_get_tool(call_obj, tools_dict)
        self.assertEqual(call_obj.name, "google_search")
        self.assertIsNotNone(tool_func)

    def test_claude_prune_thoughts_history_hygiene(self):
        """Test that pruning thoughts from Claude model turns never leaves empty parts."""
        mock_event = MagicMock()
        mock_event.role = "model"
        only_thought = MagicMock()
        only_thought.thought = True
        mock_event.content.parts = [only_thought]

        mock_context = MagicMock()
        mock_context.session.events = [mock_event]

        shared_logic.prune_thoughts_from_history(mock_context)
        self.assertEqual(len(mock_event.content.parts), 1)
        self.assertEqual(mock_event.content.parts[0].text, "[Thinking completed]")

    def test_claude_pricing_rate_card(self):
        """Test Claude pricing rate card lookup."""
        pricing = shared_logic.get_pricing()
        self.assertIn("claude-sonnet-5", pricing)
        rate = pricing["claude-sonnet-5"]
        self.assertEqual(rate["input"], 2.00)
        self.assertEqual(rate["output"], 10.00)

if __name__ == '__main__':
    unittest.main()
