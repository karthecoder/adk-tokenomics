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

    def test_evaluate_tool_and_skill_routing(self):
        query = "What are the local rules and quiet hours for Zurich?"
        response = "In Zurich, quiet hours are enforced from 10 PM. Emergency is 112."
        res = shared_logic.evaluate_tool_and_skill_routing(query, response, ["activate_skill(name='zurich-travel')"])
        self.assertIn("zurich-travel", res["expected_skills"])
        self.assertEqual(res["skill_score"], 5.0)
        self.assertEqual(res["tool_score"], 5.0)
        self.assertEqual(res["verdict"], "PERFECT MATCH 🎯")

if __name__ == '__main__':
    unittest.main()
