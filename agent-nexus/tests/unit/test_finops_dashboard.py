import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import server

class TestFinOpsDashboard(unittest.TestCase):
    
    def setUp(self):
        self.handler = MagicMock(spec=server.AgentNexusHandler)
        self.handler.fetch_finops_summary = server.AgentNexusHandler.fetch_finops_summary.__get__(self.handler)
        self.handler._empty_finops_summary = server.AgentNexusHandler._empty_finops_summary.__get__(self.handler)

    @patch('google.cloud.bigquery.Client')
    def test_fetch_finops_summary_success(self, mock_bq_client):
        mock_client_inst = MagicMock()
        mock_bq_client.return_value = mock_client_inst
        mock_client_inst.project = "vertexai-demo-ltfpzhaw"

        # Mock query 1: Groupings by model and app
        row_google = MagicMock()
        row_google.model_name = "Gemini 3.5 Flash"
        row_google.app_name = "caching_app"
        row_google.turns = 10
        row_google.input_tokens = 50000
        row_google.cached_tokens = 150000
        row_google.output_tokens = 4000
        row_google.thinking_tokens = 1000
        row_google.total_cost = 0.045

        row_claude = MagicMock()
        row_claude.model_name = "claude-sonnet-5"
        row_claude.app_name = "compaction_app"
        row_claude.turns = 5
        row_claude.input_tokens = 80000
        row_claude.cached_tokens = 0
        row_claude.output_tokens = 2500
        row_claude.thinking_tokens = 500
        row_claude.total_cost = 0.250

        mock_groups_job = MagicMock()
        mock_groups_job.result.return_value = [row_claude, row_google]

        # Mock query 2: Timeline daily rows
        row_t1 = MagicMock()
        row_t1.date_label = "2026-08-27"
        row_t1.turns = 15
        row_t1.daily_tokens = 287500
        row_t1.daily_cost = 0.295

        mock_timeline_job = MagicMock()
        mock_timeline_job.result.return_value = [row_t1]

        mock_client_inst.query.side_effect = [mock_groups_job, mock_timeline_job]

        result = self.handler.fetch_finops_summary(timeframe='all', provider='all')

        self.assertEqual(result["status"], "success")
        kpis = result["kpis"]
        self.assertAlmostEqual(kpis["total_spend"], 0.295, places=3)
        self.assertEqual(kpis["total_tokens"], 288000)
        self.assertEqual(kpis["total_input"], 130000)
        self.assertEqual(kpis["total_cached"], 150000)
        self.assertEqual(kpis["total_output"], 65000 - 58500) # 6500
        self.assertEqual(kpis["total_thinking"], 1500)
        self.assertEqual(kpis["total_turns"], 15)
        self.assertEqual(kpis["top_provider"], "Anthropic Claude")
        self.assertGreater(kpis["optimization_savings_dollars"], 0.0)

        # Provider breakdown check
        pb = result["provider_breakdown"]
        self.assertIn("Google Gemini", pb)
        self.assertIn("Anthropic Claude", pb)
        self.assertAlmostEqual(pb["Google Gemini"]["spend"], 0.045, places=3)
        self.assertAlmostEqual(pb["Anthropic Claude"]["spend"], 0.250, places=3)

        # Matrix rows check
        matrix = result["matrix_rows"]
        self.assertEqual(len(matrix), 2)
        self.assertEqual(matrix[0]["provider"], "Anthropic Claude")
        self.assertEqual(matrix[1]["provider"], "Google Gemini")

    @patch('google.cloud.bigquery.Client')
    def test_fetch_finops_summary_empty_fallback(self, mock_bq_client):
        mock_client_inst = MagicMock()
        mock_bq_client.return_value = mock_client_inst
        mock_client_inst.project = "vertexai-demo-ltfpzhaw"

        mock_groups_job = MagicMock()
        mock_groups_job.result.return_value = []
        mock_timeline_job = MagicMock()
        mock_timeline_job.result.return_value = []
        mock_client_inst.query.side_effect = [mock_groups_job, mock_timeline_job]

        result = self.handler.fetch_finops_summary(timeframe='today', provider='google')
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["kpis"]["total_spend"], 0.0)
        self.assertEqual(result["matrix_rows"], [])

if __name__ == '__main__':
    unittest.main()
