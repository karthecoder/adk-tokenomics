#!/usr/bin/env python3
"""
Test & Inspection Script for Google ADK BigQuery Agent Analytics Plugin.
Runs 4 agent scenarios (Naive, Caching, Compaction, Skills) through the official
BigQueryAgentAnalyticsPlugin and inspects the exact schema, views, and JSON payloads logged to BigQuery.
"""

import asyncio
import os
import sys
import time
import json
from google.genai import types
import google.auth
from google.cloud import bigquery

# Add current workspace to path
sys.path.append(os.path.abspath("agent-nexus"))
sys.path.append(os.path.abspath("agent-nexus/app"))

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig
)

# Import the 4 scenario agents
from naive_app.agent import naive_agent
from caching_app.agent import caching_agent
from compaction_app.agent import compaction_agent
from skills_app.agent import skills_agent

PROJECT_ID = "vertexai-demo-ltfpzhaw"
DATASET_ID = "bq_adk_ds"
TABLE_ID = "adk_agent_events"

os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

async def run_scenario(runner, session_service, app_name, query_text):
    session_id = f"test_session_{app_name}_{int(time.time())}"
    print(f"\n========================================================")
    print(f"▶️ RUNNING SCENARIO: {app_name}")
    print(f"   Query: {query_text}")
    print(f"   Session: {session_id}")
    print(f"========================================================")

    await session_service.create_session(app_name=app_name, user_id="test_user", session_id=session_id)
    
    msg = types.Content(role="user", parts=[types.Part.from_text(text=query_text)])
    
    async for event in runner.run_async(user_id="test_user", session_id=session_id, new_message=msg):
        if event.is_final_response():
            parts = getattr(event.content, "parts", [])
            resp_text = parts[0].text if parts and hasattr(parts[0], "text") else str(event.content)
            print(f"💬 Agent Response ({app_name}): {resp_text[:120]}...\n")

def inspect_bigquery_results():
    print("\n" + "="*70)
    print("🔍 INSPECTING BIGQUERY DATASET & SCHEMA")
    print(f"   Project: {PROJECT_ID} | Dataset: {DATASET_ID}")
    print("="*70)

    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    # 1. List Tables and Views
    tables = list(client.list_tables(dataset_ref))
    print(f"\n📁 Tables & Views in `{DATASET_ID}` ({len(tables)} found):")
    for t in tables:
        print(f"  - [{t.table_type}] {t.table_id}")

    # 2. Inspect Main Events Table Schema
    print(f"\n📋 Schema for Table `{TABLE_ID}`:")
    table = client.get_table(f"{dataset_ref}.{TABLE_ID}")
    for field in table.schema:
        print(f"  • {field.name:20} | Type: {field.field_type:10} | Mode: {field.mode}")

    # 3. Query sample rows from raw events table
    print("\n" + "-"*70)
    print("🔬 SAMPLE ROWS FROM RAW `agent_events` TABLE (Latest 3 events):")
    print("-"*70)
    query_events = f"""
        SELECT timestamp, event_type, agent, session_id,
               JSON_QUERY(content, '$') as raw_content,
               JSON_QUERY(attributes, '$') as raw_attributes,
               JSON_QUERY(latency_ms, '$') as raw_latency
        FROM `{dataset_ref}.{TABLE_ID}`
        ORDER BY timestamp DESC
        LIMIT 3
    """
    rows = client.query(query_events).result()
    for idx, r in enumerate(rows):
        print(f"\n[Event #{idx+1}] Type: {r['event_type']} | Agent: {r['agent']} | Time: {r['timestamp']}")
        print(f"  Attributes (Tokens/Metadata): {r['raw_attributes']}")
        print(f"  Latency: {r['raw_latency']}")
        print(f"  Content: {str(r['raw_content'])[:200]}...")

    # 4. Query from LLM_RESPONSE View
    views = [t.table_id for t in tables if t.table_type == "VIEW"]
    llm_view = None
    for v in views:
        if "llm_response" in v.lower():
            llm_view = v
            break

    if llm_view:
        print("\n" + "-"*70)
        print(f"📊 QUERYING ADK VIEW `{llm_view}`:")
        print("-"*70)
        query_view = f"""
            SELECT * FROM `{dataset_ref}.{llm_view}`
            ORDER BY timestamp DESC
            LIMIT 3
        """
        try:
            view_rows = client.query(query_view).result()
            for idx, r in enumerate(view_rows):
                print(f"\n[Turn #{idx+1}] Agent: {r.get('agent')} | Model: {r.get('model_version')}")
                print(f"  • Prompt Tokens:     {r.get('usage_prompt_tokens')}")
                print(f"  • Cached Tokens:     {r.get('usage_cached_tokens')}")
                print(f"  • Completion Tokens: {r.get('usage_completion_tokens')}")
                print(f"  • Total Tokens:      {r.get('usage_total_tokens')}")
                print(f"  • Cache Hit Rate:    {r.get('context_cache_hit_rate')}")
                print(f"  • Total Latency:     {r.get('total_ms')} ms")
        except Exception as e:
            print(f"  [WARN] View query error: {e}")

async def main():
    print("🚀 Initializing Google ADK BigQueryAgentAnalyticsPlugin ...")
    
    # Configure BigQuery Logger
    logger_config = BigQueryLoggerConfig(
        table_id=TABLE_ID,
        batch_size=1,
        batch_flush_interval=0.5,
        create_views=True,
        view_prefix="v"
    )

    bq_plugin = BigQueryAgentAnalyticsPlugin(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        config=logger_config,
        location="US"
    )

    session_service = InMemorySessionService()

    scenarios = [
        ("naive_app", naive_agent, "What is the population and weather in Tokyo?"),
        ("caching_app", caching_agent, "Compare travel highlights for Paris and London."),
        ("compaction_app", compaction_agent, "Give me a 3-day itinerary for Rome."),
        ("skills_app", skills_agent, "What are the top attractions in New York?")
    ]

    for app_name, agent_obj, query_text in scenarios:
        runner = Runner(
            agent=agent_obj,
            app_name=app_name,
            session_service=session_service,
            plugins=[bq_plugin]
        )
        await run_scenario(runner, session_service, app_name, query_text)

    print("\n⏳ Flushing BigQueryAgentAnalyticsPlugin buffer (waiting 5 seconds)...")
    await asyncio.sleep(5)
    
    # Close/flush plugin
    if hasattr(bq_plugin, "close"):
        await bq_plugin.close()
    elif hasattr(bq_plugin, "_flush"):
        await bq_plugin._flush()

    await asyncio.sleep(3)

    # Inspect BigQuery
    inspect_bigquery_results()

if __name__ == "__main__":
    asyncio.run(main())
