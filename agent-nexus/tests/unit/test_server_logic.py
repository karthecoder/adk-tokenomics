import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project roots to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import server

class TestServerLogic(unittest.TestCase):
    
    def setUp(self):
        # Create a mock instance of our request handler
        # We override standard initialization to avoid network/socket binding
        self.handler = MagicMock(spec=server.AgentNexusHandler)
        self.handler.fetch_metrics_from_bq = server.AgentNexusHandler.fetch_metrics_from_bq.__get__(self.handler)
        self.handler.fetch_sessions_from_bq = server.AgentNexusHandler.fetch_sessions_from_bq.__get__(self.handler)
        self.handler.fetch_local_fallback = server.AgentNexusHandler.fetch_local_fallback.__get__(self.handler)

    @patch('google.cloud.bigquery.Client')
    def test_fetch_sessions_success(self, mock_bq_client):
        # Mock BigQuery Client response for sessions
        mock_client_inst = MagicMock()
        mock_bq_client.return_value = mock_client_inst
        mock_client_inst.project = "test-project"
        
        # Mock Row values
        row1 = MagicMock()
        row1.session_id = "session-999"
        row1.start_time = "2026-08-05T12:00:00"
        
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [row1]
        mock_client_inst.query.return_value = mock_query_job
        
        # Execute sessions query
        sessions = self.handler.fetch_sessions_from_bq()
        
        # Verify call & results structure
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_id"], "session-999")
        self.assertEqual(sessions[0]["start_time"], "2026-08-05T12:00:00")
        mock_client_inst.query.assert_called_once()

    @patch('google.cloud.bigquery.Client')
    def test_fetch_metrics_global_success(self, mock_bq_client):
        # Mock BigQuery Client response for aggregates & history
        mock_client_inst = MagicMock()
        mock_bq_client.return_value = mock_client_inst
        mock_client_inst.project = "test-project"
        
        # Mock aggregates query response
        row_agg = MagicMock()
        row_agg.app_name = "naive_app"
        row_agg.turns = 3
        row_agg.input = 100000
        row_agg.cached = 0
        row_agg.output = 5000
        row_agg.thinking = 1024
        row_agg.cost = 0.15
        
        # Mock history query response
        row_hist = MagicMock()
        row_hist.app_name = "naive_app"
        row_hist.prompt_tokens = 30000
        row_hist.cached_tokens = 0
        row_hist.output_tokens = 1500
        row_hist.thinking_tokens = 512
        row_hist.estimated_cost = 0.05
        row_hist.timestamp = "2026-08-05T12:05:00"
        
        mock_query_job_agg = MagicMock()
        mock_query_job_agg.result.return_value = [row_agg]
        
        mock_query_job_hist = MagicMock()
        mock_query_job_hist.result.return_value = [row_hist]
        
        # Set query call to return aggregates then history query job
        mock_client_inst.query.side_effect = [mock_query_job_agg, mock_query_job_hist]
        
        # Execute global metrics fetch
        data = self.handler.fetch_metrics_from_bq(session_id="global")
        
        # Verify structure & calculations
        self.assertIn("metrics", data)
        self.assertIn("turns", data)
        self.assertIn("simulations", data)
        
        # Verify metrics aggregates mapping
        self.assertEqual(data["metrics"]["naive_app"]["turns"], 3)
        self.assertEqual(data["metrics"]["naive_app"]["input"], 100000)
        self.assertEqual(data["metrics"]["naive_app"]["thinking"], 1024)
        self.assertEqual(data["metrics"]["naive_app"]["cost"], 0.15)
        
        # Verify simulated costs based on pricing rates
        # 100,000 prompt tokens + 5,000 output tokens
        # Gemini 3.5 Flash rate: prompt = 1.50 / 1M ($0.15), output = 9.00 / 1M ($0.045). Total = $0.195
        self.assertAlmostEqual(data["simulations"]["Gemini 3.5 Flash"], 0.195)

    @patch('google.cloud.bigquery.Client')
    def test_fetch_metrics_bq_fallback(self, mock_bq_client):
        # Make BQ Client raise exception (triggering fallback)
        mock_bq_client.side_effect = Exception("BigQuery connection blocked")
        
        # Mock local file reading in fetch_local_fallback
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', unittest.mock.mock_open(read_data='{"naive_app": {"input": 50000, "cached": 0, "output": 2000, "thinking": 512, "cost": 0.07, "turns": 2}}')):
            mock_exists.return_value = True
            
            data = self.handler.fetch_metrics_from_bq(session_id="global")
            
            # Verify structure still returned correctly from local fallback
            self.assertIn("metrics", data)
            self.assertEqual(data["metrics"]["naive_app"]["turns"], 2)
            self.assertEqual(data["metrics"]["naive_app"]["thinking"], 512)
            self.assertEqual(len(data["turns"]), 0)  # history empty in local fallback
            
            # Simulated costs computed properly from local aggregates
            # 50,000 prompt + 2,000 output. Gemini 3.5 Flash: (50000 * 1.50/1M) + (2000 * 9.00/1M) = 0.075 + 0.018 = 0.093
            self.assertAlmostEqual(data["simulations"]["Gemini 3.5 Flash"], 0.093)

if __name__ == '__main__':
    unittest.main()
