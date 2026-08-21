import os
import subprocess
import glob
import json
import sys

def run_evals():
    print("==========================================================")
    print(" Running ADK Agent Evaluations...")
    print(" Target Dataset: tests/eval/datasets/travel_planner_eval.json")
    print(" Target Config:  tests/eval/eval_config.yaml")
    print("==========================================================")
    
    # Run the eval command
    cmd = [
        "agents-cli", "eval", "run",
        "--dataset", "tests/eval/datasets/travel_planner_eval.json",
        "--config", "tests/eval/eval_config.yaml"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Evaluation run failed: {e}")
        sys.exit(1)
        
    # Locate the newest results file
    results_dir = "artifacts/grade_results"
    json_files = glob.glob(os.path.join(results_dir, "results_*.json"))
    if not json_files:
        print("[ERROR] No result JSON files found.")
        sys.exit(1)
        
    newest_file = max(json_files, key=os.path.getmtime)
    print(f"\nParsing newest evaluation report: {newest_file}\n")
    
    with open(newest_file, "r") as f:
        data = json.load(f)
        
    summary_metrics = data.get("summary_metrics", [])
    case_results = data.get("eval_case_results", [])
    
    # Print Tabular Summary of Metrics
    print("+" + "-"*40 + "+" + "-"*15 + "+" + "-"*15 + "+")
    print(f"| {'Metric Name':<38} | {'Valid Cases':<13} | {'Mean Score':<13} |")
    print("+" + "-"*40 + "+" + "-"*15 + "+" + "-"*15 + "+")
    for metric in summary_metrics:
        name = metric.get("metric_name", "")
        valid = metric.get("num_cases_valid", 0)
        mean = metric.get("mean_score")
        mean_str = f"{mean:.4f}" if mean is not None else "Error/None"
        print(f"| {name:<38} | {valid:<13} | {mean_str:<13} |")
    print("+" + "-"*40 + "+" + "-"*15 + "+" + "-"*15 + "+")
    
    print("\nDetailed Per-Case Results:")
    for result in case_results:
        case_idx = result.get("eval_case_index", 0)
        # Find the query
        cases_list = data.get("evaluation_dataset", [])
        prompt_text = ""
        if cases_list and len(cases_list) > 0:
            eval_cases = cases_list[0].get("eval_cases", [])
            if case_idx < len(eval_cases):
                parts = eval_cases[case_idx].get("prompt", {}).get("parts", [])
                if parts:
                    prompt_text = parts[0].get("text", "")
                    
        candidates = result.get("response_candidate_results", [])
        if not candidates:
            continue
            
        metric_results = candidates[0].get("metric_results", {})
        
        print(f"\nCase {case_idx + 1}: Query: '{prompt_text}'")
        for m_name, m_res in metric_results.items():
            score = m_res.get("score")
            explanation = m_res.get("explanation") or "N/A"
            error = m_res.get("error_message")
            if error:
                print(f"  - {m_name:<25}: [ERROR] {error}")
            else:
                score_str = f"{score:.1f}" if score is not None else "None"
                print(f"  - {m_name:<25}: Score={score_str:<5} | Explanation: {explanation[:120]}...")

if __name__ == "__main__":
    run_evals()
