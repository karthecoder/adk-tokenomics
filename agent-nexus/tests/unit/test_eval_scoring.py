import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import shared_logic

class TestEvalScoring(unittest.TestCase):

    def test_default_eval_benchmarks(self):
        benchmarks = shared_logic.DEFAULT_EVAL_BENCHMARKS
        self.assertGreaterEqual(len(benchmarks), 5)
        for b in benchmarks:
            self.assertIn("id", b)
            self.assertIn("title", b)
            self.assertIn("query", b)

    def test_judge_response_heuristic_fallback(self):
        query = "Plan a trip to Paris."
        response = """# Paris Trip
* Hotel: Grand Paris Resort
* Transportation: Metro
* Emergency: 112
Recommended because it is very convenient."""
        score = shared_logic.judge_response(query, response)
        self.assertIn("quality", score)
        self.assertIn("accuracy", score)
        self.assertIn("reasoning", score)
        self.assertIn("composite", score)
        self.assertIn("explanation", score)
        self.assertGreaterEqual(score["quality"], 1.0)
        self.assertLessEqual(score["quality"], 5.0)

    def test_quality_per_dollar_calculation(self):
        cost = 0.002
        composite_score = 4.8
        q_per_dollar = round(composite_score / max(cost, 0.00001), 1)
        self.assertEqual(q_per_dollar, 2400.0)

if __name__ == '__main__':
    unittest.main()
