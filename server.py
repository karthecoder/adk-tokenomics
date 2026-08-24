#!/usr/bin/env python3
"""
Custom Python HTTP server for Agent Nexus dashboard.
Handles static serving and routes API POST calls to run_benchmark.py.
"""

import datetime
import http.server
import json
import os
import subprocess
import sys
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
from dotenv import load_dotenv

# Ensure working directory is always the root project directory containing index.html
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

# Load central .env file
load_dotenv()

# Import shared logic from agent-nexus
sys.path.append(os.path.join(ROOT_DIR, 'agent-nexus'))
import shared_logic

def get_clear_cutoff():
    cutoff_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent-nexus', '.clear_cutoff')
    if os.path.exists(cutoff_path):
        try:
            with open(cutoff_path, 'r') as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    return None

def set_clear_cutoff(iso_timestamp):
    cutoff_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent-nexus', '.clear_cutoff')
    with open(cutoff_path, 'w') as f:
        f.write(iso_timestamp)

# Simulation Pricing Models Map
PRICING_MODELS = {
    "Gemini 3.5 Flash": {
        "prompt": 1.50 / 1000000,
        "cached": 0.15 / 1000000,
        "output": 9.00 / 1000000
    },
    "Gemini 3.6 Flash": {
        "prompt": 1.50 / 1000000,
        "cached": 0.15 / 1000000,
        "output": 9.00 / 1000000
    },
    "Gemini 3.7 Flash": {
        "prompt": 2.00 / 1000000,
        "cached": 0.20 / 1000000,
        "output": 12.00 / 1000000
    },
    "Claude Sonnet 5": {
        "prompt": 2.00 / 1000000,
        "cached": 0.20 / 1000000,
        "output": 10.00 / 1000000
    }
}

class AgentNexusHandler(http.server.SimpleHTTPRequestHandler):
    def fetch_metrics_from_bq(self, session_id="global"):
        from google.cloud import bigquery
        from google.cloud.exceptions import NotFound
        
        default_metrics = {
            "naive_app": {"name": "1. Naive Monolithic (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0},
            "caching_app": {"name": "2. Context Caching (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0},
            "compaction_app": {"name": "3. History Compaction (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0},
            "skills_app": {"name": "4. Modular Skills (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0}
        }
        
        try:
            client = bigquery.Client()
            project = client.project
            dataset_id = "bq_adk_ds"
            try:
                client.get_dataset(f"{project}.{dataset_id}")
            except NotFound:
                dataset_id = "karticn_adk_demo"
                try:
                    client.get_dataset(f"{project}.{dataset_id}")
                except NotFound:
                    return self.fetch_local_fallback()
                    
            table_id = "token_consumption_logs"
            full_table_id = f"{project}.{dataset_id}.{table_id}"
            
            try:
                client.get_table(full_table_id)
            except NotFound:
                return self.fetch_local_fallback()
                
            cutoff = get_clear_cutoff()
            where_conds = []
            params = []
            if session_id and session_id != "global":
                where_conds.append("session_id = @session_id")
                params.append(bigquery.ScalarQueryParameter("session_id", "STRING", session_id))
            if cutoff:
                where_conds.append("timestamp > @clear_cutoff")
                params.append(bigquery.ScalarQueryParameter("clear_cutoff", "TIMESTAMP", cutoff))
                
            where_clause = "WHERE " + " AND ".join(where_conds) if where_conds else ""
                
            # Query Aggregates
            query_agg = f"""
                SELECT 
                  app_name,
                  COUNT(*) as turns,
                  SUM(prompt_tokens) as input,
                  SUM(cached_tokens) as cached,
                  SUM(output_tokens) as output,
                  SUM(COALESCE(thinking_tokens, 0)) as thinking,
                  SUM(estimated_cost) as cost
                FROM `{full_table_id}`
                {where_clause}
                GROUP BY app_name
            """
            job_config = bigquery.QueryJobConfig(query_parameters=params)
            query_job = client.query(query_agg, job_config=job_config)
            results_agg = query_job.result()
            
            metrics = {
                "naive_app": {"name": "1. Naive Monolithic", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
                "caching_app": {"name": "2. Context Caching", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
                "compaction_app": {"name": "3. History Compaction", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
                "skills_app": {"name": "4. Modular Skills", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0}
            }
            
            total_prompt = 0
            total_cached = 0
            total_output = 0
            
            for row in results_agg:
                app_name = row.app_name
                if app_name in metrics:
                    metrics[app_name]["turns"] = int(row.turns or 0)
                    metrics[app_name]["input"] = int(row.input or 0)
                    metrics[app_name]["cached"] = int(row.cached or 0)
                    metrics[app_name]["output"] = int(row.output or 0)
                    metrics[app_name]["thinking"] = int(getattr(row, "thinking", 0) or 0)
                    metrics[app_name]["cost"] = float(row.cost or 0.0)
                    
                    total_prompt += int(row.input or 0)
                    total_cached += int(row.cached or 0)
                    total_output += int(row.output or 0)
            
            # Query Turn History
            query_history = f"""
                SELECT app_name, prompt_tokens, cached_tokens, output_tokens, COALESCE(thinking_tokens, 0) as thinking_tokens, estimated_cost, timestamp
                FROM `{full_table_id}`
                {where_clause}
                ORDER BY timestamp ASC
            """
            query_job_history = client.query(query_history, job_config=job_config)
            results_history = query_job_history.result()
            
            turns = []
            for row in results_history:
                turns.append({
                    "app_name": str(row.app_name),
                    "prompt_tokens": int(row.prompt_tokens),
                    "cached_tokens": int(row.cached_tokens),
                    "output_tokens": int(row.output_tokens),
                    "thinking_tokens": int(getattr(row, "thinking_tokens", 0) or 0),
                    "estimated_cost": float(row.estimated_cost),
                    "timestamp": row.timestamp.isoformat() if hasattr(row.timestamp, "isoformat") else str(row.timestamp)
                })
                
            # Compute Simulations
            simulations = {}
            for model_name, rates in PRICING_MODELS.items():
                simulated_cost = (
                    (total_prompt - total_cached) * rates["prompt"] +
                    total_cached * rates["cached"] +
                    total_output * rates["output"]
                )
                simulations[model_name] = float(simulated_cost)
                
            res_payload = {
                "metrics": metrics,
                "turns": turns,
                "simulations": simulations
            }
            if not hasattr(self, "_metrics_cache"):
                AgentNexusHandler._metrics_cache = {}
            AgentNexusHandler._metrics_cache[session_id] = res_payload
            return res_payload
            
        except Exception as e:
            print(f"[ERROR] fetch_metrics_from_bq error: {e}", flush=True)
            if hasattr(AgentNexusHandler, "_metrics_cache") and session_id in AgentNexusHandler._metrics_cache:
                return AgentNexusHandler._metrics_cache[session_id]
            return self.fetch_local_fallback()

    def fetch_local_fallback(self):
        default_metrics = {
            "naive_app": {"name": "1. Naive Monolithic", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
            "caching_app": {"name": "2. Context Caching", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
            "compaction_app": {"name": "3. History Compaction", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
            "skills_app": {"name": "4. Modular Skills", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0}
        }
        metrics_path = os.path.join('agent-nexus', 'live_metrics.json')
        metrics = default_metrics
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r') as f:
                    metrics = json.load(f)
            except Exception:
                pass
                
        # Run what-if simulations on local sum totals
        simulations = {}
        total_prompt = 0
        total_cached = 0
        total_output = 0
        for app in metrics.values():
            total_prompt += app.get("input", 0)
            total_cached += app.get("cached", 0)
            total_output += app.get("output", 0)
            
        for model_name, rates in PRICING_MODELS.items():
            simulated_cost = (
                (total_prompt - total_cached) * rates["prompt"] +
                total_cached * rates["cached"] +
                total_output * rates["output"]
            )
            simulations[model_name] = float(simulated_cost)
            
        return {
            "metrics": metrics,
            "turns": [],
            "simulations": simulations
        }

    def fetch_sessions_from_bq(self):
        from google.cloud import bigquery
        from google.cloud.exceptions import NotFound
        
        try:
            client = bigquery.Client()
            project = client.project
            dataset_id = "bq_adk_ds"
            try:
                client.get_dataset(f"{project}.{dataset_id}")
            except NotFound:
                dataset_id = "karticn_adk_demo"
                try:
                    client.get_dataset(f"{project}.{dataset_id}")
                except NotFound:
                    return []
                    
            table_id = "token_consumption_logs"
            full_table_id = f"{project}.{dataset_id}.{table_id}"
            
            try:
                client.get_table(full_table_id)
            except NotFound:
                return []
                
            cutoff = get_clear_cutoff()
            where_clause = f"WHERE timestamp > @clear_cutoff" if cutoff else ""
            params = [bigquery.ScalarQueryParameter("clear_cutoff", "TIMESTAMP", cutoff)] if cutoff else []
                
            query = f"""
                SELECT session_id, MIN(timestamp) as start_time
                FROM `{full_table_id}`
                {where_clause}
                GROUP BY session_id
                ORDER BY start_time DESC
            """
            job_config = bigquery.QueryJobConfig(query_parameters=params) if params else None
            query_job = client.query(query, job_config=job_config)
            results = query_job.result()
            
            sessions = []
            for row in results:
                sessions.append({
                    "session_id": str(row.session_id),
                    "start_time": row.start_time.isoformat() if hasattr(row.start_time, "isoformat") else str(row.start_time)
                })
            return sessions
        except Exception as e:
            print(f"[ERROR] fetch_sessions_from_bq error: {e}", flush=True)
            return []

    def clear_bq_table(self):
        from google.cloud import bigquery
        from google.cloud.exceptions import NotFound
        try:
            client = bigquery.Client()
            project = client.project
            dataset_id = "bq_adk_ds"
            try:
                client.get_dataset(f"{project}.{dataset_id}")
            except NotFound:
                dataset_id = "karticn_adk_demo"
                try:
                    client.get_dataset(f"{project}.{dataset_id}")
                except NotFound:
                    return
            
            table_id = "token_consumption_logs"
            full_table_id = f"{project}.{dataset_id}.{table_id}"
            
            try:
                client.get_table(full_table_id)
            except NotFound:
                return
                
            query = f"DELETE FROM `{full_table_id}` WHERE TRUE"
            query_job = client.query(query)
            query_job.result()
            print(f"[BQ] Truncated table {full_table_id}", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to truncate BQ table: {e}", flush=True)

    def is_dashboard_route(self, path):
        dashboard_exact = [
            '/', '/index.html', '/styles.css', '/app.js',
            '/api/clear-metrics', '/api/sessions', '/api/models',
            '/api/config', '/api/benchmark',
            '/agent-nexus/live_metrics.json', '/live_metrics.json'
        ]
        return path in dashboard_exact

    def is_adk_route(self, path):
        return not self.is_dashboard_route(path)

    def proxy_to_adk(self):
        target_path = self.path
        if target_path.startswith('/adk'):
            target_path = target_path[4:]
            if not target_path or not target_path.startswith('/'):
                target_path = '/' + target_path

        target_url = f"http://127.0.0.1:8082{target_path}"
        try:
            req_headers = {k: v for k, v in self.headers.items() if k.lower() not in ['host', 'accept-encoding']}
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            req = urllib.request.Request(target_url, data=body, headers=req_headers, method=self.command)
            with urllib.request.urlopen(req, timeout=35) as resp:
                self.send_response(resp.status)
                headers_dict = dict(resp.headers)
                content_type = headers_dict.get('Content-Type', '')
                
                resp_body = resp.read()
                
                # Replace base href to /adk/ if HTML response so Angular SPA routes & chunks resolve cleanly
                if 'text/html' in content_type:
                    try:
                        html_str = resp_body.decode('utf-8', errors='ignore')
                        if '<base href="./">' in html_str:
                            html_str = html_str.replace('<base href="./">', '<base href="/adk/">', 1)
                        elif '<head>' in html_str and '<base' not in html_str:
                            html_str = html_str.replace('<head>', '<head><base href="/adk/">', 1)
                        resp_body = html_str.encode('utf-8')
                    except Exception as ex:
                        print(f"[BASE INJECT ERROR] {ex}", flush=True)

                for k, v in resp.headers.items():
                    if k.lower() not in ['transfer-encoding', 'content-length', 'content-encoding']:
                        self.send_header(k, v)
                self.send_header('Content-Length', str(len(resp_body)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ['transfer-encoding', 'content-length', 'content-encoding']:
                    self.send_header(k, v)
            err_body = e.read()
            self.send_header('Content-Length', str(len(err_body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            print(f"[PROXY ERROR] {target_url}: {e}", flush=True)
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Bad Gateway", "details": str(e)}).encode('utf-8'))

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if self.is_adk_route(path):
            self.proxy_to_adk()
            return
        # Handle CORS preflight
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if self.is_adk_route(path):
            self.proxy_to_adk()
            return
            
        if path == '/agent-nexus/live_metrics.json' or path == '/live_metrics.json':
            session_id = query_params.get('session_id', ['global'])[0]
            print(f">>> Fetching live metrics from BigQuery (session_id={session_id})...")
            try:
                metrics_data = self.fetch_metrics_from_bq(session_id=session_id)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(metrics_data).encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to serve BQ metrics: {e}", flush=True)
                super().do_GET()
        elif path == '/api/sessions':
            print(">>> Fetching session list from BigQuery...")
            try:
                sessions = self.fetch_sessions_from_bq()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(sessions).encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to serve BQ sessions: {e}", flush=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        elif path == '/api/models':
            cfg = shared_logic.load_models_config()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(cfg).encode('utf-8'))

        elif path == '/api/config':
            model_id = os.environ.get("DEMO_MODEL_NAME", "publishers/google/models/gemini-3.5-flash")
            thinking_budget = os.environ.get("THINKING_BUDGET", "0")
            max_output_tokens = os.environ.get("MAX_OUTPUT_TOKENS", "8192")
            clean_name = model_id.split('/')[-1]
            clean_name = clean_name.replace('-preview', '').replace('-', ' ').title()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "model_id": model_id,
                "model_name": clean_name,
                "thinking_budget": thinking_budget,
                "max_output_tokens": max_output_tokens
            }).encode('utf-8'))
        else:
            super().do_GET()

    def do_DELETE(self):
        url_parts = urllib.parse.urlparse(self.path)
        if url_parts.path == '/api/models':
            params = urllib.parse.parse_qs(url_parts.query)
            model_id = params.get('id', [None])[0]
            if not model_id:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    try:
                        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                        model_id = data.get('id')
                    except Exception:
                        pass

            if not model_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Missing model id"}).encode('utf-8'))
                return

            cfg = shared_logic.load_models_config()
            models = cfg.get("models", [])
            new_models = [m for m in models if m.get("id") != model_id]
            cfg["models"] = new_models

            with open(shared_logic.MODELS_CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)

            shared_logic.PRICING = shared_logic.get_pricing()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "deleted": model_id}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def update_env_file(self, key, value):
        env_path = '.env'
        if not os.path.exists(env_path):
            env_path = os.path.join('agent-nexus', '.env')
        
        os.environ[key] = str(value)
        
        lines = []
        key_found = False
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        lines.append(f"{key}={value}\n")
                        key_found = True
                    else:
                        lines.append(line)
        if not key_found:
            lines.append(f"\n{key}={value}\n")
            
        with open(env_path, 'w') as f:
            f.writelines(lines)
        print(f"[ENV] Updated {key}={value} in {env_path}", flush=True)

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if self.is_adk_route(path):
            self.proxy_to_adk()
            return

        if self.path == '/api/clear-metrics':
            print(">>> Clearing BigQuery and local metrics logs...")
            try:
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                set_clear_cutoff(now_iso)
                
                # Clear BQ Table
                self.clear_bq_table()
                
                default_metrics = {
                    "naive_app": {"name": "1. Naive Monolithic (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
                    "caching_app": {"name": "2. Context Caching (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
                    "compaction_app": {"name": "3. History Compaction (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
                    "skills_app": {"name": "4. Modular Skills (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0}
                }
                zero_payload = {
                    "metrics": default_metrics,
                    "turns": [],
                    "simulations": {
                        "Gemini 3.5 Flash": 0.0,
                        "Gemini 3.6 Flash": 0.0,
                        "Gemini 3.7 Flash": 0.0,
                        "Claude Sonnet 5": 0.0
                    }
                }
                AgentNexusHandler._metrics_cache = {"global": zero_payload}
                
                # Clear local backup
                metrics_path = os.path.join('agent-nexus', 'live_metrics.json')
                with open(metrics_path, 'w') as f:
                    json.dump(default_metrics, f, indent=2)
                
                dashboard_path = os.path.join('agent-nexus', 'live_dashboard.md')
                default_dashboard = """# Agent Nexus: Live Playground Travel Planner Dashboard
*This dashboard tracks token consumption in real-time as you chat with the four travel planner scenario apps in the playground.*

## 📊 Live Scenario Comparison Table
*(Awaiting your conversation turns in the travel planning playground to begin calculating metrics...)*

| Scenario | Turns | Input (Fresh) | Input (Cached) | Output | Est. Cost | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. Naive Monolithic (Pro) | 0 | 0 | 0 | 0 | $0.00000 | Idle ⚪ |
| 2. Context Caching (Pro) | 0 | 0 | 0 | 0 | $0.00000 | Idle ⚪ |
| 3. History Compaction (Pro) | 0 | 0 | 0 | 0 | $0.00000 | Idle ⚪ |
| 4. Modular Skills (Pro) | 0 | 0 | 0 | 0 | $0.00000 | Idle ⚪ |
"""
                with open(dashboard_path, 'w') as f:
                    f.write(default_dashboard)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

        elif self.path == '/api/models_config_raw':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                payload = json.loads(post_data.decode('utf-8'))
                raw_str = payload.get('raw_json')
                if not raw_str:
                    parsed_cfg = payload
                else:
                    parsed_cfg = json.loads(raw_str)
                
                if not isinstance(parsed_cfg, dict) or "models" not in parsed_cfg:
                    raise ValueError("JSON root must be an object containing a 'models' array.")

                with open(shared_logic.MODELS_CONFIG_PATH, "w") as f:
                    json.dump(parsed_cfg, f, indent=2)

                shared_logic.PRICING = shared_logic.get_pricing()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "config": parsed_cfg}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

        elif self.path == '/api/models':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                model_entry = json.loads(post_data.decode('utf-8'))
                m_id = model_entry.get('id')
                if not m_id:
                    raise ValueError("Model entry must contain an 'id'")
                
                cfg = shared_logic.load_models_config()
                models = cfg.get("models", [])
                
                updated = False
                for idx, m in enumerate(models):
                    if m.get('id') == m_id:
                        models[idx] = model_entry
                        updated = True
                        break
                if not updated:
                    models.append(model_entry)
                
                cfg["models"] = models
                with open(shared_logic.MODELS_CONFIG_PATH, "w") as f:
                    json.dump(cfg, f, indent=2)

                shared_logic.PRICING = shared_logic.get_pricing()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "model": model_entry}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

        elif self.path == '/api/set_model':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                payload = json.loads(post_data.decode('utf-8'))
                model_name = payload.get('model_name')
                if model_name:
                    self.update_env_file("DEMO_MODEL_NAME", model_name)
                    
                    cfg = shared_logic.load_models_config()
                    matched = next((m for m in cfg.get("models", []) if m.get("id") == model_name or m.get("name") == model_name), None)
                    if matched:
                        if "thinking_budget" in matched:
                            self.update_env_file("THINKING_BUDGET", matched["thinking_budget"])
                        if "max_output_tokens" in matched:
                            self.update_env_file("MAX_OUTPUT_TOKENS", matched["max_output_tokens"])

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "model_name": model_name}).encode('utf-8'))
                else:
                    raise ValueError("Missing model_name parameter")
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

        elif self.path == '/api/set_thinking':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                payload = json.loads(post_data.decode('utf-8'))
                thinking_budget = payload.get('thinking_budget')
                if thinking_budget is not None:
                    self.update_env_file("THINKING_BUDGET", thinking_budget)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "thinking_budget": thinking_budget}).encode('utf-8'))
                else:
                    raise ValueError("Missing thinking_budget parameter")
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

        elif self.path == '/api/set_maxtokens':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                payload = json.loads(post_data.decode('utf-8'))
                max_output_tokens = payload.get('max_output_tokens')
                if max_output_tokens is not None:
                    self.update_env_file("MAX_OUTPUT_TOKENS", max_output_tokens)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "max_output_tokens": max_output_tokens}).encode('utf-8'))
                else:
                    raise ValueError("Missing max_output_tokens parameter")
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

        elif self.path == '/api/run-benchmark':
            print(">>> Received request to run programmatic ADK benchmark...")
            
            try:
                # Execute the benchmark runner script
                process = subprocess.run(
                    [sys.executable, 'run_benchmark.py'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Check for script output results
                results_path = 'benchmark_results.json'
                if os.path.exists(results_path):
                    with open(results_path, 'r') as f:
                        data = json.load(f)
                    
                    # Append subprocess console output logs for live visualizer terminal
                    data["logs"] = process.stdout + "\n" + process.stderr
                else:
                    data = {
                        "status": "error",
                        "message": "Benchmark finished but results file was not found.",
                        "logs": process.stdout + "\n" + process.stderr
                    }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
                
            except subprocess.TimeoutExpired:
                self.send_response(504)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "The ADK benchmark execution timed out."
                }).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": f"Server encountered internal error: {str(e)}"
                }).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

def run_server(port):
    server_address = ('', port)
    httpd = http.server.ThreadingHTTPServer(server_address, AgentNexusHandler)
    print(f"[SYS] Custom Agent Nexus Server running at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SYS] Server shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
