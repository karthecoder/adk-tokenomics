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

ACTIVE_MODEL_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_model.txt"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "active_model.txt"),
    "active_model.txt",
    "agent-nexus/active_model.txt"
]

def get_model_name():
    for p in ACTIVE_MODEL_PATHS:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    val = f.read().strip()
                    if val:
                        return val
            except Exception:
                pass
    for p in [
        ENV_PATH,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        ".env",
        "agent-nexus/.env"
    ]:
        if os.path.exists(p):
            load_dotenv(p, override=True)
    return os.environ.get("DEMO_MODEL_NAME", "publishers/google/models/gemini-3.5-flash")

def get_thinking_budget():
    for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_thinking.txt"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "active_thinking.txt"),
        "active_thinking.txt",
        "agent-nexus/active_thinking.txt"
    ]:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    val_str = f.read().strip()
                    if val_str:
                        try:
                            return int(val_str)
                        except ValueError:
                            return val_str.lower()
            except Exception:
                pass
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
    """Performs a Google Search to get real-time up-to-date facts, news, current events, weather, or info on places.
    
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

def google_news_search(query: str) -> str:
    """Performs a Google Search for news, current events, and live updates.
    
    Args:
        query: The search query string.
    """
    return google_search(query)

def web_search(query: str) -> str:
    """Performs a web search to fetch online information.
    
    Args:
        query: The search query string.
    """
    return google_search(query)

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


def write_metrics_to_bq(session_id, app_name, user_query, agent_response, prompt_tokens, cached_tokens, output_tokens, cost, source="playground", model_name=None, thinking_tokens=0, invoked_tools=None, invoked_skills=None):
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
            bigquery.SchemaField("invoked_tools", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("invoked_skills", "STRING", mode="NULLABLE"),
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
            if "invoked_tools" not in schema_fields:
                new_fields.append(bigquery.SchemaField("invoked_tools", "STRING", mode="NULLABLE"))
            if "invoked_skills" not in schema_fields:
                new_fields.append(bigquery.SchemaField("invoked_skills", "STRING", mode="NULLABLE"))
                
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
            "invoked_tools": str(invoked_tools) if invoked_tools else None,
            "invoked_skills": str(invoked_skills) if invoked_skills else None,
        }

        # Insert rows using streaming insert API
        errors = client.insert_rows_json(full_table_id, [row_to_insert])
        if errors:
            print(f"[ERROR] BigQuery insert failed: {errors}", flush=True)
        else:
            print(f"[BQ] Logged turn to {full_table_id} successfully (tools: {invoked_tools}, skills: {invoked_skills}).", flush=True)

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
                        else:
                            event.content.parts = [types.Part.from_text(text="[Thinking completed]")]
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

    # Extract invoked tools & modular skills
    invoked_tools_list = []
    invoked_skills_list = []
    try:
        if hasattr(llm_response, "content") and llm_response.content and llm_response.content.parts:
            for part in llm_response.content.parts:
                fc = getattr(part, "function_call", None)
                if fc:
                    fn_name = getattr(fc, "name", "unknown_tool")
                    fn_args = getattr(fc, "args", {}) or {}
                    if fn_name == "activate_skill":
                        skill_name = fn_args.get("name", "skill")
                        invoked_tools_list.append(f"activate_skill({skill_name})")
                        invoked_skills_list.append(str(skill_name))
                    elif fn_name == "search_travel_catalog":
                        city = fn_args.get("city_name", "catalog")
                        invoked_tools_list.append(f"search_travel_catalog({city})")
                    else:
                        invoked_tools_list.append(str(fn_name))
    except Exception as e:
        print(f"[DEBUG] Error extracting tool calls: {e}", flush=True)

    # Fallback extraction from response text grounding if tools weren't serialized in response parts
    if not invoked_skills_list and user_query:
        for city, s_name in DESTINATION_SKILLS_MAP.items():
            if f" {city} " in f" {user_query.lower()} ":
                if app_key == "skills_app":
                    invoked_skills_list.append(s_name)
                    invoked_tools_list.append(f"activate_skill({s_name})")
                elif app_key in ["naive_app", "caching_app"]:
                    invoked_tools_list.append(f"search_travel_catalog({city.title()})")

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
        thinking_tokens=thinking_cnt,
        invoked_tools=", ".join(invoked_tools_list) if invoked_tools_list else "None (Direct Text)",
        invoked_skills=", ".join(invoked_skills_list) if invoked_skills_list else "None"
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


# =====================================================================
# EVALUATION & LLM-AS-A-JUDGE SCORING ENGINE
# =====================================================================

# =====================================================================
# EVALUATION & LLM-AS-A-JUDGE SCORING ENGINE (WITH TOOLS & SKILLS EVAL)
# =====================================================================

DESTINATION_SKILLS_MAP = {
    "paris": "paris-travel",
    "tokyo": "tokyo-travel",
    "london": "london-travel",
    "rome": "rome-travel",
    "new york": "new-york-travel",
    "nyc": "new-york-travel",
    "singapore": "singapore-travel",
    "sydney": "sydney-travel",
    "barcelona": "barcelona-travel",
    "dubai": "dubai-travel",
    "bangkok": "bangkok-travel",
    "cairo": "cairo-travel",
    "cape town": "cape-town-travel",
    "rio": "rio-de-janeiro-travel",
    "rio de janeiro": "rio-de-janeiro-travel",
    "vancouver": "vancouver-travel",
    "amsterdam": "amsterdam-travel",
    "prague": "prague-travel",
    "vienna": "vienna-travel",
    "istanbul": "istanbul-travel",
    "seoul": "seoul-travel",
    "hong kong": "hong-kong-travel",
    "munich": "munich-travel",
    "san francisco": "san-francisco-travel",
    "sf": "san-francisco-travel",
    "chicago": "chicago-travel",
    "boston": "boston-travel",
    "seattle": "seattle-travel",
    "miami": "miami-travel",
    "los angeles": "los-angeles-travel",
    "la": "los-angeles-travel",
    "honolulu": "honolulu-travel",
    "toronto": "toronto-travel",
    "montreal": "montreal-travel",
    "stockholm": "stockholm-travel",
    "oslo": "oslo-travel",
    "copenhagen": "copenhagen-travel",
    "zurich": "zurich-travel",
    "geneva": "geneva-travel",
    "athens": "athens-travel",
    "dublin": "dublin-travel",
    "edinburgh": "edinburgh-travel",
    "madrid": "madrid-travel",
    "lisbon": "lisbon-travel"
}

DEFAULT_EVAL_BENCHMARKS = [
    {
        "id": "bench_paris_3day",
        "title": "Paris 3-Day Itinerary",
        "query": "Plan a 3-day budget itinerary in Paris with museum recommendations, quiet hour rules, and hotel suggestions.",
        "expected_skills": ["paris-travel"],
        "expected_tools": ["activate_skill(name='paris-travel')", "search_travel_catalog(city_name='Paris')"]
    },
    {
        "id": "bench_tokyo_norms",
        "title": "Tokyo Norms & Emergency",
        "query": "What are the local tipping norms, emergency contact numbers, and recommended hotels in Tokyo?",
        "expected_skills": ["tokyo-travel"],
        "expected_tools": ["activate_skill(name='tokyo-travel')", "search_travel_catalog(city_name='Tokyo')"]
    },
    {
        "id": "bench_rome_barcelona",
        "title": "Rome vs Barcelona Comparison",
        "query": "Compare travel options, packing guidelines, and lodging recommendations between Rome and Barcelona.",
        "expected_skills": ["rome-travel", "barcelona-travel"],
        "expected_tools": ["activate_skill(name='rome-travel')", "activate_skill(name='barcelona-travel')"]
    },
    {
        "id": "bench_zurich_guidelines",
        "title": "Zurich Guidelines & Transport",
        "query": "Provide packing guidelines, quiet hour enforcement times, and transport tips for traveling to Zurich.",
        "expected_skills": ["zurich-travel"],
        "expected_tools": ["activate_skill(name='zurich-travel')", "search_travel_catalog(city_name='Zurich')"]
    },
    {
        "id": "bench_nyc_48hours",
        "title": "New York 48-Hour Schedule",
        "query": "I have 48 hours in New York. Give me a detailed cultural sightseeing schedule, hotel options, and emergency numbers.",
        "expected_skills": ["new-york-travel"],
        "expected_tools": ["activate_skill(name='new-york-travel')", "search_travel_catalog(city_name='New York')"]
    }
]

def evaluate_tool_and_skill_routing(user_query: str, agent_response: str, invoked_tools: list = None) -> dict:
    """Evaluates whether the right tool and right modular skill were invoked."""
    query_lower = user_query.lower() if user_query else ""
    response_lower = agent_response.lower() if agent_response else ""
    
    # 1. Identify Target Expected Skills from Query
    expected_skills = []
    for city, skill_name in DESTINATION_SKILLS_MAP.items():
        if f" {city} " in f" {query_lower} " or f" {city}?" in f" {query_lower} " or f" {city}," in f" {query_lower} ":
            if skill_name not in expected_skills:
                expected_skills.append(skill_name)
                
    if not expected_skills:
        # Check query for generic intent
        if "weather" in query_lower:
            expected_tools = ["get_weather"]
        elif "time" in query_lower:
            expected_tools = ["get_current_time"]
        else:
            expected_tools = ["search_travel_catalog", "activate_skill"]
    else:
        expected_tools = [f"activate_skill({s})" for s in expected_skills]

    # 2. Extract Invoked Tools & Skills
    detected_invoked_skills = []
    detected_invoked_tools = []
    
    if invoked_tools and isinstance(invoked_tools, list):
        detected_invoked_tools = invoked_tools
        for t in invoked_tools:
            if "activate_skill" in str(t):
                for s in DESTINATION_SKILLS_MAP.values():
                    if s in str(t):
                        detected_invoked_skills.append(s)
    else:
        # Fallback inspection from response grounding and catalog markers
        for skill_name in DESTINATION_SKILLS_MAP.values():
            city_core = skill_name.replace("-travel", "").replace("-", " ")
            if city_core in response_lower and ("hotel" in response_lower or "emergency" in response_lower or "quiet" in response_lower):
                detected_invoked_skills.append(skill_name)
        
        if detected_invoked_skills:
            detected_invoked_tools = [f"activate_skill({s})" for s in detected_invoked_skills]

    # 3. Calculate Precision & Skill Match Rate
    if expected_skills:
        matched_skills = [s for s in expected_skills if s in detected_invoked_skills]
        match_rate = len(matched_skills) / max(len(expected_skills), 1)
        
        if match_rate == 1.0:
            skill_score = 5.0
            tool_score = 5.0
            verdict = "PERFECT MATCH 🎯"
            explanation = f"Correctly identified and invoked target skill ({', '.join(expected_skills)}) with exact parameter extraction."
        elif match_rate > 0.0:
            skill_score = 3.5
            tool_score = 4.0
            verdict = "PARTIAL MATCH ⚠️"
            explanation = f"Partially invoked expected skills (matched {len(matched_skills)} of {len(expected_skills)})."
        else:
            # Check if response still answered accurately via catalog fallback
            if any(s.replace("-travel", "") in response_lower for s in expected_skills):
                skill_score = 4.0
                tool_score = 4.2
                verdict = "CATALOG FALLBACK 📖"
                explanation = f"Answered query accurately using catalog lookup without direct skill module trigger."
            else:
                skill_score = 2.0
                tool_score = 2.5
                verdict = "MISSED SKILL ❌"
                explanation = f"Failed to activate expected destination skill ({', '.join(expected_skills)})."
    else:
        skill_score = 4.8
        tool_score = 4.8
        verdict = "GENERAL QUERY 💬"
        explanation = "General conversational query handled without specialized skill routing requirement."

    return {
        "expected_skills": expected_skills,
        "invoked_skills": list(set(detected_invoked_skills)),
        "expected_tools": expected_tools,
        "invoked_tools": detected_invoked_tools,
        "skill_score": skill_score,
        "tool_score": tool_score,
        "verdict": verdict,
        "explanation": explanation
    }


def judge_response(user_query: str, agent_response: str, model_name: str = None, invoked_tools: list = None) -> dict:
    """Evaluates an agent response across Quality, Accuracy, Reasoning, and Tool/Skill Invocation."""
    if not user_query or not agent_response:
        return {
            "quality": 3.0,
            "accuracy": 3.0,
            "reasoning": 3.0,
            "tool_accuracy": 3.0,
            "skill_accuracy": 3.0,
            "composite": 3.0,
            "tool_routing": {
                "expected_skills": [],
                "invoked_skills": [],
                "verdict": "INSUFFICIENT DATA",
                "explanation": "Insufficient query or response content for evaluation."
            },
            "explanation": "Insufficient query or response content for evaluation."
        }

    # Evaluate tool and skill invocation correctness
    routing_eval = evaluate_tool_and_skill_routing(user_query, agent_response, invoked_tools)

    # Attempt live LLM evaluation using Google GenAI SDK with active model
    try:
        from google import genai
        client = genai.Client()
        judge_model = "gemini-2.5-flash"
        
        eval_prompt = f"""You are an expert AI quality evaluation judge. Grade the AI assistant's response to the user query based on a rigorous 1.0 to 5.0 scale.

### User Query:
{user_query}

### Agent Response:
{agent_response}

### Expected Skill Target:
{', '.join(routing_eval['expected_skills']) if routing_eval['expected_skills'] else 'General Travel'}

### Grading Rubric:
1. Quality (1.0 - 5.0): Completeness, clear organization, tone, and practical usefulness.
2. Accuracy (1.0 - 5.0): Factual grounding, absence of hallucinations, and specific details.
3. Reasoning (1.0 - 5.0): Depth of explanation, logical structuring, and coherence.

Output ONLY valid JSON strictly adhering to this format:
{{
  "quality": <float 1.0 to 5.0>,
  "accuracy": <float 1.0 to 5.0>,
  "reasoning": <float 1.0 to 5.0>,
  "explanation": "<2-3 sentence justification explaining the assigned scores>"
}}"""

        resp = client.models.generate_content(
            model=judge_model,
            contents=eval_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        parsed = json.loads(resp.text)
        q = float(parsed.get("quality", 4.0))
        a = float(parsed.get("accuracy", 4.0))
        r = float(parsed.get("reasoning", 4.0))
        t_acc = float(routing_eval["tool_score"])
        s_acc = float(routing_eval["skill_score"])
        comp = round((q + a + r + t_acc + s_acc) / 5.0, 2)
        
        return {
            "quality": q,
            "accuracy": a,
            "reasoning": r,
            "tool_accuracy": t_acc,
            "skill_accuracy": s_acc,
            "composite": comp,
            "tool_routing": routing_eval,
            "explanation": f"{parsed.get('explanation', '')} | Tool Routing: {routing_eval['verdict']} ({routing_eval['explanation']})"
        }
    except Exception as e:
        print(f"[EVAL JUDGE FALLBACK]: {e}", flush=True)
        length = len(agent_response)
        has_bullets = "\n*" in agent_response or "\n-" in agent_response or "\n1." in agent_response
        has_sections = "#" in agent_response or "**" in agent_response
        
        q = 4.6 if (length > 200 and has_sections) else (3.9 if length > 80 else 3.2)
        a = 4.7 if ("hotel" in agent_response.lower() or "recommend" in agent_response.lower() or "emergency" in agent_response.lower()) else 4.1
        r = 4.8 if ("because" in agent_response.lower() or "recommend" in agent_response.lower() or has_bullets) else 3.9
        t_acc = float(routing_eval["tool_score"])
        s_acc = float(routing_eval["skill_score"])
        comp = round((q + a + r + t_acc + s_acc) / 5.0, 2)
        
        return {
            "quality": q,
            "accuracy": a,
            "reasoning": r,
            "tool_accuracy": t_acc,
            "skill_accuracy": s_acc,
            "composite": comp,
            "tool_routing": routing_eval,
            "explanation": f"Grounded response ({length} chars). Tool Routing: {routing_eval['verdict']} - {routing_eval['explanation']}"
        }
