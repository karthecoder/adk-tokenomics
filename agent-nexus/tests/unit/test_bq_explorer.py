import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import server

class TestBigQueryExplorer(unittest.TestCase):
    
    def setUp(self):
        self.handler = MagicMock(spec=server.AgentNexusHandler)
        self.handler.fetch_bq_explorer_logs = server.AgentNexusHandler.fetch_bq_explorer_logs.__get__(self.handler)
        self.handler.fetch_bq_stats = server.AgentNexusHandler.fetch_bq_stats.__get__(self.handler)

    @patch('google.cloud.bigquery.Client')
    def test_fetch_bq_explorer_logs_success(self, mock_bq_client):
        mock_client_inst = MagicMock()
        mock_bq_client.return_value = mock_client_inst
        mock_client_inst.project = "vertexai-demo-ltfpzhaw"

        # Mock count result
        mock_count_row = MagicMock()
        mock_count_row.total = 42
        mock_count_job = MagicMock()
        mock_count_job.result.return_value = [mock_count_row]

        # Mock data rows (all 14 columns)
        mock_data_row = MagicMock()
        mock_data_row.timestamp = "2026-08-27T12:00:00Z"
        mock_data_row.session_id = "sess-123"
        mock_data_row.app_name = "skills_app"
        mock_data_row.user_query = "What is the capital of France?"
        mock_data_row.agent_response = "Paris is the capital."
        mock_data_row.prompt_tokens = 1200
        mock_data_row.cached_tokens = 0
        mock_data_row.output_tokens = 250
        mock_data_row.thinking_tokens = 0
        mock_data_row.estimated_cost = 0.003
        mock_data_row.source = "adk_playground"
        mock_data_row.model_name = "Gemini 3.5 Flash"
        mock_data_row.invoked_tools = "activate_skill(paris-travel)"
        mock_data_row.invoked_skills = "paris-travel"

        mock_data_job = MagicMock()
        mock_data_job.result.return_value = [mock_data_row]

        mock_client_inst.query.side_effect = [mock_count_job, mock_data_job]

        result = self.handler.fetch_bq_explorer_logs(limit=25, offset=0, app_name="skills_app", search="Paris")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_rows"], 42)
        self.assertEqual(len(result["rows"]), 1)
        row = result["rows"][0]
        self.assertEqual(row["session_id"], "sess-123")
        self.assertEqual(row["app_name"], "skills_app")
        self.assertEqual(row["prompt_tokens"], 1200)
        self.assertEqual(row["invoked_skills"], "paris-travel")
        self.assertEqual(row["invoked_tools"], "activate_skill(paris-travel)")

    @patch('google.cloud.bigquery.Client')
    def test_fetch_bq_stats_success(self, mock_bq_client):
        mock_client_inst = MagicMock()
        mock_bq_client.return_value = mock_client_inst
        mock_client_inst.project = "vertexai-demo-ltfpzhaw"

        mock_stats_row = MagicMock()
        mock_stats_row.total_turns = 150
        mock_stats_row.total_cost = 1.2543
        mock_stats_row.total_input = 500000
        mock_stats_row.total_cached = 350000
        mock_stats_row.total_output = 45000
        mock_stats_row.unique_sessions = 12

        mock_job = MagicMock()
        mock_job.result.return_value = [mock_stats_row]
        mock_client_inst.query.return_value = mock_job

        stats = self.handler.fetch_bq_stats()

        self.assertEqual(stats["total_turns"], 150)
        self.assertEqual(stats["total_cost"], 1.2543)
        self.assertEqual(stats["total_input"], 500000)
        self.assertEqual(stats["total_cached"], 350000)
        self.assertEqual(stats["total_output"], 45000)
        self.assertEqual(stats["unique_sessions"], 12)

if __name__ == '__main__':
    unittest.main()
