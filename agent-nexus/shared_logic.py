import datetime
import json
import os
from google.genai import types
import google.auth
from dotenv import load_dotenv

# Load central .env file
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(ENV_PATH, override=True)

# Setup Vertex AI credentials and location defaults
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    os.environ["GOOGLE_CLOUD_PROJECT"] = "vertexai-demo-ltfpzhaw"

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def get_model_name():
    load_dotenv(ENV_PATH, override=True)
    return os.environ.get("DEMO_MODEL_NAME", "publishers/google/models/gemini-3.5-flash")

def get_thinking_budget():
    load_dotenv(ENV_PATH, override=True)
    val = os.environ.get("THINKING_BUDGET", "0")
    val_str = str(val).strip()
    try:
        return int(val_str)
    except ValueError:
        return val_str.lower()

def get_max_output_tokens():
    load_dotenv(ENV_PATH, override=True)
    val = os.environ.get("MAX_OUTPUT_TOKENS", "8192")
    try:
        return int(val)
    except ValueError:
        return 8192

DEFAULT_MODEL = get_model_name()
THINKING_BUDGET = get_thinking_budget()
MAX_OUTPUT_TOKENS = get_max_output_tokens()

MODELS_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models_config.json")

def load_models_config():
    if os.path.exists(MODELS_CONFIG_PATH):
        try:
            with open(MODELS_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load models_config.json: {e}", flush=True)
    return {"models": []}

def get_pricing():
    pricing_map = {
        "flash": {"input": 1.50, "cached": 0.15, "output": 9.00},
        "pro": {"input": 2.00, "cached": 0.20, "output": 12.00},
        "lite": {"input": 0.30, "cached": 0.03, "output": 2.50}
    }
    cfg = load_models_config()
    for m in cfg.get("models", []):
        m_id = m.get("id")
        pricing = m.get("pricing", {})
        if m_id and pricing:
            rates = {
                "input": float(pricing.get("input", 1.50)),
                "cached": float(pricing.get("cached", 0.15)),
                "output": float(pricing.get("output", 9.00))
            }
            pricing_map[m_id] = rates
            m_name = m.get("name")
            if m_name:
                pricing_map[m_name] = rates
    return pricing_map

PRICING = get_pricing()

# Import large travel catalog documentation from prompts
from prompts import CATALOG_TEXT

# Tools definitions
def google_search(query: str) -> str:
    """Performs a Google Search to get real-time up-to-date facts, current events, weather, or info on places.
    
    Args:
        query: The search query string.
    """
    from google import genai
    client = genai.Client()
    response = client.models.generate_content(
        model="publishers/google/models/gemini-3.5-flash",
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    return response.text

def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather."""
    return "It's 60 degrees and foggy in SF."

def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city."""
    return "The current time is 10:45 AM PST."

def search_travel_catalog(city_name: str) -> str:
    """Searches the destination travel catalog and returns recommendations for a specific city.
    
    Args:
        city_name: The name of the city to search (e.g. Paris, Tokyo, London).
        
    Returns:
        The travel tips, hotels, and recommendations for the requested city.
    """
    cleaned_name = city_name.strip().title()
    return f"""Destination Entry: {cleaned_name}
Recommended Hotels:
- The Grand {cleaned_name} Palace (Luxury)
- Central Stay {cleaned_name} (Boutique)
Local Rules & Guidelines:
- Respect quiet hours after 10 PM.
- Standard tipping is included in service charges.
Key Attractions:
- Historic Downtown Plaza
- Scenic City Skyline Viewpoint
Packing Tip: Carry comfortable walking shoes and a universal plug adapter."""


def discover_skills(skills_dir: str = None) -> str:
    """Discovers available skills and builds the XML skills catalog string."""
    if not skills_dir:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        skills_dir = os.path.join(base_dir, "skills")
    
    catalog_parts = ["<available_skills>"]
    if os.path.exists(skills_dir):
        for folder_name in sorted(os.listdir(skills_dir)):
            folder_path = os.path.join(skills_dir, folder_name)
            skill_md_path = os.path.join(folder_path, "SKILL.md")
            if os.path.isdir(folder_path) and os.path.exists(skill_md_path):
                description = f"Access travel recommendations and tips for {folder_name.replace('-travel', '').title()}."
                try:
                    with open(skill_md_path, "r") as f:
                        lines = f.readlines()
                    if len(lines) > 0 and lines[0].strip() == "---":
                        yaml_lines = []
                        for line in lines[1:]:
                            if line.strip() == "---":
                                break
                            yaml_lines.append(line)
                        for yl in yaml_lines:
                            if yl.startswith("description:"):
                                description = yl.replace("description:", "").strip()
                                break
                except Exception as e:
                    print(f"[DEBUG] Error reading SKILL.md: {e}", flush=True)
                
                catalog_parts.append(f"  <skill>\n    <name>{folder_name}</name>\n    <description>{description}</description>\n    <location>{skill_md_path}</location>\n  </skill>")
    catalog_parts.append("</available_skills>")
    return "\n".join(catalog_parts)


def activate_skill(name: str) -> str:
    """Activates a skill by loading its SKILL.md content formatted in standard XML wrapping.
    
    Args:
        name: The exact name of the skill to activate (e.g., tokyo-travel, paris-travel).
        
    Returns:
        The full instruction payload of the activated skill.
    """
    cleaned_name = name.strip().lower()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skill_md_path = os.path.join(base_dir, "skills", cleaned_name, "SKILL.md")
    
    if not os.path.exists(skill_md_path):
        return f"Error: Skill '{name}' not found."
        
    try:
        with open(skill_md_path, "r") as f:
            content = f.read()
            
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()
                
        return f"""<skill_content name="{cleaned_name}">
{content}
Skill directory: {os.path.join(base_dir, "skills", cleaned_name)}
Relative paths in this skill are relative to the skill directory.
</skill_content>"""
    except Exception as e:
        return f"Error: Failed to activate skill '{name}': {e}"


def write_metrics_to_bq(session_id, app_name, user_query, agent_response, prompt_tokens, cached_tokens, output_tokens, cost, source="playground", model_name=None, thinking_tokens=0):
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
    import datetime

    try:
        client = bigquery.Client()
        project = client.project
        dataset_id = "bq_adk_ds"
        table_id = "token_consumption_logs"
        full_table_id = f"{project}.{dataset_id}.{table_id}"
        
        # Verify dataset exists, if not, fallback to karticn_adk_demo
        try:
            client.get_dataset(f"{project}.{dataset_id}")
        except NotFound:
            dataset_id = "karticn_adk_demo"
            full_table_id = f"{project}.{dataset_id}.{table_id}"
            try:
                client.get_dataset(f"{project}.{dataset_id}")
            except NotFound:
                # If neither exists, create bq_adk_ds
                dataset_id = "bq_adk_ds"
                full_table_id = f"{project}.{dataset_id}.{table_id}"
                dataset = bigquery.Dataset(f"{project}.{dataset_id}")
                dataset.location = "us-central1"
                client.create_dataset(dataset)
                print(f"[BQ] Created dataset: {dataset_id}", flush=True)

        # Schema definition
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("app_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_query", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("agent_response", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("prompt_tokens", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("cached_tokens", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("output_tokens", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("thinking_tokens", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("estimated_cost", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("model_name", "STRING", mode="NULLABLE"),
        ]

        # Verify table exists, if not, create it
        try:
            table = client.get_table(full_table_id)
            schema_fields = [f.name for f in table.schema]
            new_fields = []
            if "model_name" not in schema_fields:
                new_fields.append(bigquery.SchemaField("model_name", "STRING", mode="NULLABLE"))
            if "thinking_tokens" not in schema_fields:
                new_fields.append(bigquery.SchemaField("thinking_tokens", "INTEGER", mode="NULLABLE"))
                
            if new_fields:
                print(f"[BQ] Schema migration: Adding {[f.name for f in new_fields]} columns to {full_table_id}", flush=True)
                table.schema = list(table.schema) + new_fields
                client.update_table(table, ["schema"])
        except NotFound:
            table = bigquery.Table(full_table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            client.create_table(table)
            print(f"[BQ] Created table: {full_table_id}", flush=True)

        # Prepare row data
        row_to_insert = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "session_id": str(session_id),
            "app_name": str(app_name),
            "user_query": str(user_query) if user_query else None,
            "agent_response": str(agent_response) if agent_response else None,
            "prompt_tokens": int(prompt_tokens),
            "cached_tokens": int(cached_tokens),
            "output_tokens": int(output_tokens),
            "thinking_tokens": int(thinking_tokens),
            "estimated_cost": float(cost),
            "source": str(source),
            "model_name": str(model_name) if model_name else str(DEFAULT_MODEL),
        }

        # Insert rows using streaming insert API
        errors = client.insert_rows_json(full_table_id, [row_to_insert])
        if errors:
            print(f"[ERROR] BigQuery insert failed: {errors}", flush=True)
        else:
            print(f"[BQ] Logged turn to {full_table_id} successfully.", flush=True)

    except Exception as e:
        print(f"[ERROR] BigQuery writing failed: {e}", flush=True)


def prune_thoughts_from_history(callback_context, **kwargs):
    """Callback to remove thought parts from conversation history before sending the next turn's prompt."""
    try:
        session = getattr(callback_context, "session", None)
        if session and hasattr(session, "events"):
            for event in session.events:
                if getattr(event, "role", None) == "model" and hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        clean_parts = [
                            p for p in event.content.parts
                            if not getattr(p, "thought", False)
                        ]
                        if clean_parts:
                            event.content.parts = clean_parts
    except Exception as e:
        print(f"[DEBUG] Pruning thoughts failed: {e}", flush=True)


def after_model_cb(callback_context, llm_response):
    # Prune thoughts from history to prevent context compounding
    prune_thoughts_from_history(callback_context)

    usage = llm_response.usage_metadata
    if not usage:
        return None
        
    prompt_cnt = getattr(usage, "prompt_token_count", 0) or 0
    cached_cnt = getattr(usage, "cached_content_token_count", 0) or 0
    output_cnt = getattr(usage, "candidates_token_count", 0) or 0
    thinking_cnt = getattr(usage, "thoughts_token_count", 0) or 0
    
    # Pricing calculations based on active model name
    model_name = get_model_name()
    rates = PRICING.get(model_name, PRICING.get("publishers/google/models/gemini-3.5-flash", PRICING["flash"]))
    cost = (
        ((prompt_cnt - cached_cnt) * rates["input"]) +
        (cached_cnt * rates["cached"]) +
        (output_cnt * rates["output"])
    ) / 1_000_000

    # Deduce the scenario app name from active agent's name
    agent_name = callback_context.agent_name.lower()
    
    # Standardize names
    if "naive" in agent_name:
        app_key = "naive_app"
    elif "cach" in agent_name:
        app_key = "caching_app"
    elif "compact" in agent_name:
        app_key = "compaction_app"
    elif "skill" in agent_name:
        app_key = "skills_app"
    else:
        app_key = "naive_app"
        
    print(f"\n[DEBUG] agent_name='{agent_name}', resolved app_key='{app_key}'", flush=True)

    # Extract query and response
    user_query = ""
    try:
        user_content = getattr(callback_context, "user_content", None)
        if user_content and getattr(user_content, "parts", None):
            parts = []
            for part in user_content.parts:
                if getattr(part, "text", None):
                    parts.append(part.text)
            user_query = " ".join(parts)
    except Exception as e:
        print(f"[DEBUG] Failed to extract query: {e}", flush=True)

    agent_response = ""
    try:
        if hasattr(llm_response, "content") and llm_response.content and llm_response.content.parts:
            parts = []
            for part in llm_response.content.parts:
                if getattr(part, "text", None) and not getattr(part, "thought", False):
                    parts.append(part.text)
            agent_response = " ".join(parts)
    except Exception as e:
        print(f"[DEBUG] Failed to extract response text: {e}", flush=True)

    session_id = "test_session"
    try:
        session_id = getattr(getattr(callback_context, "session", None), "id", "test_session")
    except Exception as e:
        print(f"[DEBUG] Failed to get session id: {e}", flush=True)

    # Log turn to BigQuery
    write_metrics_to_bq(
        session_id=session_id,
        app_name=app_key,
        user_query=user_query,
        agent_response=agent_response,
        prompt_tokens=prompt_cnt,
        cached_tokens=cached_cnt,
        output_tokens=output_cnt,
        cost=cost,
        source="playground",
        thinking_tokens=thinking_cnt
    )

    # Persist live metrics in local JSON file (backward compatibility/fallback)
    metrics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_metrics.json")
    default_metrics = {
        "naive_app": {"name": "1. Naive Monolithic (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
        "caching_app": {"name": "2. Context Caching (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
        "compaction_app": {"name": "3. History Compaction (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
        "skills_app": {"name": "4. Modular Skills (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0}
    }
    
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
        except Exception:
            metrics = default_metrics
    else:
        metrics = default_metrics

    if app_key in metrics:
        metrics[app_key]["input"] += prompt_cnt
        metrics[app_key]["cached"] += cached_cnt
        metrics[app_key]["output"] += output_cnt
        metrics[app_key]["cost"] += cost
        metrics[app_key]["turns"] += 1
        if "thinking" not in metrics[app_key]:
            metrics[app_key]["thinking"] = 0
        metrics[app_key]["thinking"] += thinking_cnt
        
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # Write unified live_dashboard.md file
    write_dashboard_report(metrics, app_key)
    return None

def write_dashboard_report(metrics, active_app):
    report_content = f"""# Agent Nexus: Live Playground Tokenomics Dashboard
*This dashboard tracks token consumption in real-time as you chat with the four scenario apps in the playground.*

## 📊 Live Scenario Comparison Table
*(The row representing the active app you just queried is highlighted below)*

| Scenario | Turns | Input (Fresh) | Input (Cached) | Output | Est. Cost | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for key, data in metrics.items():
        is_active = (key == active_app)
        status_lbl = "**ACTIVE 🟢**" if is_active else "Idle ⚪"
        fresh_in = data["input"] - data["cached"]
        
        report_content += f"""| {data["name"]} | {data["turns"]} | {fresh_in:,} | {data["cached"]:,} | {data["output"]:,} | ${data["cost"]:.5f} | {status_lbl} |\n"""
        
    # Cost savings logic
    n_cost = metrics["naive_app"]["cost"]
    c_cost = metrics["caching_app"]["cost"]
    s_cost = metrics["skills_app"]["cost"]
    
    report_content += f"""
---

## 💡 Live Presentation Talking Points
"""
    if n_cost > 0 and c_cost > 0:
        savings = ((n_cost - c_cost) / n_cost) * 100
        report_content += f"""* **Context Caching:** Enabling caching reduced cumulative cost from `${n_cost:.5f}` to `${c_cost:.5f}` (**{savings:.1f}% savings**). Observe how the Cached Input count increases after your first turn!\n"""
    else:
        report_content += f"""* **Context Caching:** Chat with both the **Naive (naive_app)** and **Caching (caching_app)** apps to see cost savings calculate in real-time.\n"""
        
    if n_cost > 0 and s_cost > 0:
        savings = ((n_cost - s_cost) / n_cost) * 100
        report_content += f"""* **Modular Skills:** Shifting context details to the `activate_skill` tool instead of stuffing it in instructions cut costs by **{savings:.1f}%**! The input footprint remained tiny on every turn.\n"""

    report_content += f"""
*Report updated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    # Write to root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root_dir, "live_dashboard.md"), "w") as f:
        f.write(report_content)
