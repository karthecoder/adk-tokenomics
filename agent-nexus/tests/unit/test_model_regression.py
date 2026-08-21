import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import app.agent
import shared_logic
from app.agent import get_model, DynamicModel
from google.adk.models.google_llm import Gemini
import google.adk.models.anthropic_llm as anthropic_llm_module
from google.adk.models.anthropic_llm import Claude
from google.genai import types
from anthropic import types as anthropic_types

class TestModelRegression(unittest.TestCase):

    def test_get_model_resolution(self):
        """Test model instantiation logic for all supported models."""
        # 1. Gemini 3.5 Flash
        with patch.object(shared_logic, 'get_model_name', return_value="publishers/google/models/gemini-3.5-flash"):
            model = get_model()
            self.assertIsInstance(model, Gemini)
            self.assertEqual(model.model, "publishers/google/models/gemini-3.5-flash")

        # 2. Gemini 3.6 Flash
        with patch.object(shared_logic, 'get_model_name', return_value="publishers/google/models/gemini-3.6-flash"):
            model = get_model()
            self.assertIsInstance(model, Gemini)
            self.assertEqual(model.model, "publishers/google/models/gemini-3.6-flash")

        # 3. Gemini 3.7 Flash
        with patch.object(shared_logic, 'get_model_name', return_value="publishers/google/models/gemini-3.7-flash"):
            model = get_model()
            self.assertIsInstance(model, Gemini)
            self.assertEqual(model.model, "publishers/google/models/gemini-3.7-flash")

        # 4. Claude Sonnet 5
        with patch.object(shared_logic, 'get_model_name', return_value="claude-sonnet-5"):
            model = get_model()
            self.assertIsInstance(model, Claude)
            self.assertEqual(model.model, "claude-sonnet-5")

    def test_anthropic_thinking_param_builder(self):
        """Test Anthropic thinking parameter builder for thinking budget = 0 and positive budget (adaptive)."""
        # Budget = 0 (Disabled)
        cfg_0 = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
        param_0 = anthropic_llm_module._build_anthropic_thinking_param(cfg_0)
        self.assertEqual(param_0["type"], "disabled")

        # Budget = 4096 (Adaptive for Claude Sonnet 5 / Opus 4.7+)
        cfg_4096 = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=4096))
        param_4096 = anthropic_llm_module._build_anthropic_thinking_param(cfg_4096)
        self.assertEqual(param_4096["type"], "adaptive")

    def test_anthropic_usage_metadata_parsing(self):
        """Test parsing of Anthropic message response into LlmResponse usage metadata including thinking tokens."""
        mock_usage = MagicMock()
        mock_usage.input_tokens = 1250
        mock_usage.output_tokens = 3400
        
        mock_details = MagicMock()
        mock_details.thinking_tokens = 2100
        mock_usage.output_tokens_details = mock_details

        mock_msg = MagicMock()
        mock_msg.content = []
        mock_msg.usage = mock_usage

        resp = app.agent._patched_message_to_generate_content_response(mock_msg)
        usage = resp.usage_metadata

        self.assertEqual(usage.prompt_token_count, 1250)
        self.assertEqual(usage.candidates_token_count, 3400)
        self.assertEqual(usage.thoughts_token_count, 2100)
        self.assertEqual(usage.total_token_count, 4650)

    def test_models_config_json_loader(self):
        """Test loading models and pricing rates dynamically from models_config.json."""
        config = shared_logic.load_models_config()
        self.assertIn("models", config)
        models = config["models"]
        self.assertGreaterEqual(len(models), 4)
        
        pricing = shared_logic.get_pricing()
        self.assertIn("claude-sonnet-5", pricing)
        self.assertIn("publishers/google/models/gemini-3.5-flash", pricing)
        self.assertIn("publishers/google/models/gemini-3.6-flash", pricing)
        self.assertIn("publishers/google/models/gemini-3.7-flash", pricing)
        
        # Verify rate fields
        claude_rate = pricing["claude-sonnet-5"]
        self.assertEqual(claude_rate["input"], 2.00)
        self.assertEqual(claude_rate["output"], 10.00)

if __name__ == '__main__':
    unittest.main()
