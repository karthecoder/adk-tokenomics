import sys
import os
import unittest
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from server import AgentNexusHandler
import shared_logic

class TestAdkFinopsNative(unittest.TestCase):

    def setUp(self):
        self.handler = AgentNexusHandler
        self.dummy_handler = type("DummyHandler", (), {
            "ACTIVE_BQ_CONFIG": {
                "project_id": "vertexai-demo-ltfpzhaw",
                "dataset_id": "bq_adk_ds",
                "table_id": "adk_agent_events",
                "view_id": "v_llm_response"
            },
            "_calc_model_cost": AgentNexusHandler._calc_model_cost,
            "get_bq_config": AgentNexusHandler.get_bq_config,
            "set_bq_config": AgentNexusHandler.set_bq_config,
            "_empty_finops_summary": AgentNexusHandler._empty_finops_summary
        })()

    def test_cost_calculation_rates(self):
        models_cfg = shared_logic.load_models_config()
        
        # Test Gemini 3.5 Flash rate calculation
        res = self.dummy_handler._calc_model_cost(
            model_name="gemini-3.5-flash",
            input_tokens=10000,
            cached_tokens=40000,
            output_tokens=1000,
            thinking_tokens=200,
            models_config=models_cfg
        )
        self.assertGreater(res["total_cost"], 0.0)
        self.assertGreater(res["savings_dollars"], 0.0)
        self.assertEqual(res["input_rate"], 0.30)
        self.assertEqual(res["cached_rate"], 0.075)

    def test_bq_config_getter_setter(self):
        self.dummy_handler.set_bq_config({
            "project_id": "test-project",
            "dataset_id": "test_ds",
            "table_id": "test_events",
            "view_id": "test_v_llm"
        })
        self.assertEqual(self.dummy_handler.ACTIVE_BQ_CONFIG["project_id"], "test-project")
        self.assertEqual(self.dummy_handler.ACTIVE_BQ_CONFIG["dataset_id"], "test_ds")
        self.assertEqual(self.dummy_handler.ACTIVE_BQ_CONFIG["table_id"], "test_events")
        self.assertEqual(self.dummy_handler.ACTIVE_BQ_CONFIG["view_id"], "test_v_llm")

    def test_empty_finops_summary_structure(self):
        empty = self.dummy_handler._empty_finops_summary("Test error")
        self.assertEqual(empty["status"], "error")
        self.assertIn("kpis", empty)
        self.assertIn("total_spend", empty["kpis"])
        self.assertIn("provider_breakdown", empty)
        self.assertIn("Google Gemini", empty["provider_breakdown"])

if __name__ == '__main__':
    unittest.main()
