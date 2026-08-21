#!/usr/bin/env python3
"""
Agent Nexus: Programmatic ADK Tokenomics Showcase
Demonstrates token consumption differences across four context design versions:
1. Naive (Monolithic Gemini 3.1 Pro, no caching, no compaction)
2. Caching (Gemini 3.1 Pro + Context Caching)
3. Compaction (Gemini 3.1 Pro + Context Compaction)
4. Routing (Gemini 3.5 Flash Lite -> Gemini 3.1 Pro Routing Stack)
"""

import asyncio
import os
import sys
import time
from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps.app import EventsCompactionConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models import Gemini
from google.genai import types

# Define pricing per million tokens
PRICING = {
    "gemini-3.1-pro-preview": {"input": 1.74, "cached": 0.174, "output": 8.70},
    "gemini-3.5-flash": {"input": 1.50, "cached": 0.15, "output": 7.50},
    "gemini-3.5-flash-lite": {"input": 0.30, "cached": 0.03, "output": 2.50}
}

# Global token counters for active run
run_metrics = []

# Generate large schema documentation to trigger caching (approx 6k tokens)
def get_large_schema():
    schema = "DATABASE SCHEMA DOCUMENTATION\n=================================\n\n"
    for i in range(1, 41):
        schema += f"""
Table {i}: user_profiles_v{i}
Description: Stores profiles and telemetry for user version {i}.
Columns:
  - id (INT, PRIMARY KEY): Unique identifier.
  - user_id (INT, FOREIGN KEY): Maps to users table.
  - display_name (VARCHAR): The username.
  - avatar_url (TEXT): Profile photo.
  - bio (TEXT): Description of user.
  - location_country (VARCHAR): Geographic region.
  - preferred_language (VARCHAR): Locale settings.
  - timezone_offset (INT): Offset from UTC.
  - created_at (TIMESTAMP): Record creation date.
  - updated_at (TIMESTAMP): Last modification date.
  - is_active (BOOLEAN): Current account status.
  - telemetry_flags (INT): Bitmask of feature toggles.
  - billing_tier (VARCHAR): Free, Premium, Enterprise.
  - storage_consumed_bytes (BIGINT): Total user data size.
  - last_login_ip (VARCHAR): IP address trace.
Constraints:
  - UNIQUE(user_id)
  - INDEX(billing_tier, is_active)
"""
    return schema

SCHEMA_TEXT = get_large_schema()

# Setup Vertex AI Environment
os.environ["GOOGLE_CLOUD_PROJECT"] = "vertexai-demo-ltfpzhaw"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

async def after_model_cb(callback_context, llm_response):
    usage = llm_response.usage_metadata
    model = llm_response.model_version
    
    # Standardize model names to pricing keys
    pricing_key = "gemini-3.5-flash"
    if "pro" in model:
        pricing_key = "gemini-3.1-pro-preview"
    elif "lite" in model:
        pricing_key = "gemini-3.5-flash-lite"
        
    if usage:
        prompt_cnt = usage.prompt_token_count or 0
        cached_cnt = usage.cached_content_token_count or 0
        output_cnt = usage.candidates_token_count or 0
        
        # Calculate cost based on pricing definition
        rates = PRICING.get(pricing_key, PRICING["gemini-3.5-flash"])
        cost = (
            ((prompt_cnt - cached_cnt) * rates["input"]) +
            (cached_cnt * rates["cached"]) +
            (output_cnt * rates["output"])
        ) / 1_000_000
        
        run_metrics.append({
            "model": pricing_key,
            "input": prompt_cnt,
            "cached": cached_cnt,
            "output": output_cnt,
            "cost": cost
        })
        
        print(f"  \033[90m[ADK Trace]\033[0m Model: \033[94m{pricing_key}\033[0m | Input: {prompt_cnt} (Cached: {cached_cnt}) | Output: {output_cnt} | Cost: ${cost:.6f}")
    return None

async def run_naive():
    global run_metrics
    run_metrics = []
    print("\n\033[91;1m=== VERSION 1: NAIVE MONOLITHIC RUN ===\033[0m")
    print("Executing standard Pro agent with no caching, no compaction...")
    
    agent = Agent(
        name="naive_pro",
        model=Gemini(model="publishers/google/models/gemini-3.1-pro-preview"),
        instruction=f"You are a database assistant. Use this schema for queries:\n{SCHEMA_TEXT}",
        after_model_callback=after_model_cb
    )
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="naive_s1")
    runner = Runner(agent=agent, app_name="app", session_service=session_service)
    
    prompts = [
        "Which table handles user profiles for version 5?",
        "What are the columns of user_profiles_v30?",
        "Write a SELECT statement targeting user_profiles_v40 display name."
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n\033[1mTurn {i}:\033[0m User: '{prompt}'")
        async for event in runner.run_async(
            user_id="user", session_id="naive_s1",
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ):
            if event.is_final_response():
                print(f"Agent: {event.content.parts[0].text[:80].strip()}...")
                
    total_cost = sum(m["cost"] for m in run_metrics)
    total_tokens = sum(m["input"] + m["output"] for m in run_metrics)
    print(f"\n\033[91;1m[SUMMARY - NAIVE]\033[0m Total Tokens: {total_tokens:,} | Total Cost: ${total_cost:.5f}")
    return run_metrics

async def run_caching():
    global run_metrics
    run_metrics = []
    print("\n\033[92;1m=== VERSION 2: NEXUS CONTEXT CACHING RUN ===\033[0m")
    print("Executing standard Pro agent with Vertex AI Context Caching Enabled...")
    
    agent = Agent(
        name="cached_pro",
        model=Gemini(model="publishers/google/models/gemini-3.1-pro-preview"),
        instruction=f"You are a database assistant. Use this schema for queries:\n{SCHEMA_TEXT}",
        after_model_callback=after_model_cb
    )
    
    # Wrap in App with context cache config
    app = App(
        name="app",
        root_agent=agent,
        context_cache_config=ContextCacheConfig(
            min_tokens=2048,
            ttl_seconds=300
        )
    )
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="cache_s1")
    runner = Runner(app=app, session_service=session_service)
    
    prompts = [
        "Which table handles user profiles for version 5?",
        "What are the columns of user_profiles_v30?",
        "Write a SELECT statement targeting user_profiles_v40 display name."
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n\033[1mTurn {i}:\033[0m User: '{prompt}'")
        async for event in runner.run_async(
            user_id="user", session_id="cache_s1",
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ):
            if event.is_final_response():
                print(f"Agent: {event.content.parts[0].text[:80].strip()}...")
                
    total_cost = sum(m["cost"] for m in run_metrics)
    total_tokens = sum(m["input"] + m["output"] for m in run_metrics)
    print(f"\n\033[92;1m[SUMMARY - CACHING]\033[0m Total Tokens: {total_tokens:,} | Total Cost: ${total_cost:.5f}")
    return run_metrics

async def run_compaction():
    global run_metrics
    run_metrics = []
    print("\n\033[93;1m=== VERSION 3: NEXUS CONTEXT COMPACTION RUN ===\033[0m")
    print("Executing agent with History Compaction to prevent token linear expansion...")
    
    agent = Agent(
        name="compact_pro",
        model=Gemini(model="publishers/google/models/gemini-3.1-pro-preview"),
        instruction=f"You are a database assistant. Use this schema for queries:\n{SCHEMA_TEXT}",
        after_model_callback=after_model_cb
    )
    
    # Wrap in App with events compaction (summarize history every 3 turns)
    app = App(
        name="app",
        root_agent=agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=4,
            overlap_size=1
        )
    )
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="compact_s1")
    runner = Runner(app=app, session_service=session_service)
    
    prompts = [
        "Which table handles user profiles for version 5?",
        "What are the columns of user_profiles_v30?",
        "Write a SELECT statement targeting user_profiles_v40 display name.",
        "Add a WHERE clause filtering location_country to 'USA'.",
        "Add billing_tier = 'Premium' filter to the query.",
        "Sort the final selection by created_at descending."
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n\033[1mTurn {i}:\033[0m User: '{prompt}'")
        async for event in runner.run_async(
            user_id="user", session_id="compact_s1",
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ):
            if event.is_final_response():
                print(f"Agent: {event.content.parts[0].text[:80].strip()}...")
                
    total_cost = sum(m["cost"] for m in run_metrics)
    total_tokens = sum(m["input"] + m["output"] for m in run_metrics)
    print(f"\n\033[93;1m[SUMMARY - COMPACTION]\033[0m Total Tokens: {total_tokens:,} | Total Cost: ${total_cost:.5f}")
    return run_metrics

async def run_routing():
    global run_metrics
    run_metrics = []
    print("\n\033[96;1m=== VERSION 4: NEXUS HYBRID MODEL ROUTING ===\033[0m")
    print("Routing formatting/lookups to Gemini 3.5 Flash Lite; routing code reviews to Pro...")
    
    # 1. Lite formatter agent
    lite_agent = Agent(
        name="lite_agent",
        model=Gemini(model="publishers/google/models/gemini-3.5-flash-lite"),
        instruction=f"Find the correct table structure and format it cleanly.\n{SCHEMA_TEXT}",
        output_key="formatted_db_info",
        after_model_callback=after_model_cb
    )
    
    # 2. Pro reasoning agent
    pro_agent = Agent(
        name="pro_agent",
        model=Gemini(model="publishers/google/models/gemini-3.1-pro-preview"),
        instruction="Review the formatted DB columns and build optimized SQL indexing commands: {formatted_db_info}",
        after_model_callback=after_model_cb
    )
    
    # Combined Sequential Workflow
    workflow = SequentialAgent(
        name="nexus_workflow",
        sub_agents=[lite_agent, pro_agent]
    )
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="routing_s1")
    runner = Runner(agent=workflow, app_name="app", session_service=session_service)
    
    prompt = "Create optimized SQL tables query for user profiles version 10 display name."
    print(f"\n\033[1mSingle Execution Workflow:\033[0m User: '{prompt}'")
    
    async for event in runner.run_async(
        user_id="user", session_id="routing_s1",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ):
        if event.is_final_response():
            print(f"Final Agent Output: {event.content.parts[0].text[:80].strip()}...")
            
    total_cost = sum(m["cost"] for m in run_metrics)
    total_tokens = sum(m["input"] + m["output"] for m in run_metrics)
    print(f"\n\033[96;1m[SUMMARY - ROUTING]\033[0m Total Tokens: {total_tokens:,} | Total Cost: ${total_cost:.5f}")
    return run_metrics

def print_final_comparison(naive, cache, compact, route):
    print("\n\033[95;1m" + "="*70)
    print("                 FINAL ADK TOKENOMICS COMPARISON REPORT")
    print("="*70 + "\033[0m")
    
    def get_summary(metrics):
        total_in = sum(m["input"] for m in metrics)
        total_cached = sum(m["cached"] for m in metrics)
        total_out = sum(m["output"] for m in metrics)
        total_cost = sum(m["cost"] for m in metrics)
        return total_in, total_cached, total_out, total_cost

    n_in, n_cache, n_out, n_cost = get_summary(naive)
    c_in, c_cache, c_out, c_cost = get_summary(cache)
    cp_in, cp_cache, cp_out, cp_cost = get_summary(compact)
    r_in, r_cache, r_out, r_cost = get_summary(route)
    
    print(f"{'Version':<22} | {'Input (Fresh)':<12} | {'Input (Cached)':<14} | {'Output':<8} | {'Est. Cost':<10}")
    print("-"*70)
    print(f"1. Naive Monolithic    | {n_in - n_cache:<12,} | {n_cache:<14,} | {n_out:<8,} | ${n_cost:.5f}")
    print(f"2. Context Caching     | {c_in - c_cache:<12,} | {c_cache:<14,} | {c_out:<8,} | ${c_cost:.5f}")
    print(f"3. Context Compaction  | {cp_in - cp_cache:<12,} | {cp_cache:<14,} | {cp_out:<8,} | ${cp_cost:.5f}")
    print(f"4. Hybrid Routing      | {r_in - r_cache:<12,} | {r_cache:<14,} | {r_out:<8,} | ${r_cost:.5f}")
    print("="*70)
    
    savings = ((n_cost - c_cost) / n_cost) * 100 if n_cost > 0 else 0
    print(f"\033[92;1m🔥 Context Caching achieved a {savings:.1f}% cost savings over Naive run!\033[0m")
    print("="*70)

async def main():
    args = sys.argv[1:]
    mode = args[0] if args else "all"
    
    if mode == "naive":
        await run_naive()
    elif mode == "caching":
        await run_caching()
    elif mode == "compaction":
        await run_compaction()
    elif mode == "routing":
        await run_routing()
    else:
        # Run all sequentially and print comparison table
        naive = await run_naive()
        await asyncio.sleep(2)
        cache = await run_caching()
        await asyncio.sleep(2)
        compact = await run_compaction()
        await asyncio.sleep(2)
        route = await run_routing()
        await asyncio.sleep(2)
        print_final_comparison(naive, cache, compact, route)

if __name__ == "__main__":
    asyncio.run(main())
