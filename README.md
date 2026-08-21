# Agent Tokenomics & Context Optimization Sandbox

Welcome to the **Agent Tokenomics & Context Optimization Sandbox**! This workspace is designed to demonstrate, benchmark, and visualize the impact of different context management techniques in generative AI agents. 

Using **Google Gemini** and the **Agent Development Kit (ADK)**, this sandbox provides a side-by-side comparison of four different agent architectures: Naive Monolithic, Context Caching, History Compaction, and Modular Skills.

---

## 📂 Project Directory Structure & File Map

Here is the complete guide to all files in this repository, broken down by component.

### 1. Root Level (Web Dashboard & Benchmarking)
These files manage the local server, data storage, and frontend dashboard for comparing tokenomics.

*   **[server.py](file:///Users/karticn/tokenomics/server.py)**: The FastAPI server that drives the dashboard. It queries BigQuery dynamically to generate aggregated statistics and handles actions like database truncation (`/api/clear-metrics`).
*   **[index.html](file:///Users/karticn/tokenomics/index.html)**: The frontend dashboard interface, loaded with modern styles and charts to visualize token counts, turns, and cost metrics in real-time.
*   **[styles.css](file:///Users/karticn/tokenomics/styles.css)**: Vanilla CSS stylesheet that powers the premium dark-themed styling, tables, and layouts for the dashboard.
*   **[app.js](file:///Users/karticn/tokenomics/app.js)**: Client-side JavaScript logic that polls `/agent-nexus/live_metrics.json` and updates the interactive graphs.
*   **[run.sh](file:///Users/karticn/tokenomics/run.sh)**: A simple bash script to boot up the FastAPI dashboard server locally on port `8000`.
*   **[run_benchmark.py](file:///Users/karticn/tokenomics/run_benchmark.py)**: Python automation script that runs simulated user conversations across the configurations to record baseline statistics.
*   **[benchmark_results.json](file:///Users/karticn/tokenomics/benchmark_results.json)**: Cache file containing the output of `run_benchmark.py`.
*   **[.env](file:///Users/karticn/tokenomics/.env)**: Central configuration file containing model identifiers (`DEMO_MODEL_NAME`), GCP project definitions, and regional settings.

### 2. `agent-nexus/` (ADK Agent Projects)
This directory houses the python backend containing the ADK agents and optimization layers.

*   **[agent-nexus/shared_logic.py](file:///Users/karticn/tokenomics/agent-nexus/shared_logic.py)**: Central utility module containing shared pricing definitions, common tools (`get_weather`), callback logging, and the BigQuery streaming function (`write_metrics_to_bq`).
*   **[agent-nexus/prompts.py](file:///Users/karticn/tokenomics/agent-nexus/prompts.py)**: Central prompt registry containing isolated system instructions, city-catalog data loaders, and instruction templates.
*   **[agent-nexus/Dockerfile](file:///Users/karticn/tokenomics/agent-nexus/Dockerfile)**: Docker configuration file used to build and package the agent service.
*   **[agent-nexus/create_skills.py](file:///Users/karticn/tokenomics/agent-nexus/create_skills.py)**: Helper script that reads the catalog definitions and outputs the 40 city skill directories conforming to the `agentskills.io` standard.

#### Agent Application Scenarios:
*   **[agent-nexus/app/agent.py](file:///Users/karticn/tokenomics/agent-nexus/app/agent.py)**: Monolithic configuration compiling all 4 scenario apps into one FastAPI context for standard runs.
*   **[agent-nexus/naive_app/agent.py](file:///Users/karticn/tokenomics/agent-nexus/naive_app/agent.py)**: Configures the **Naive Monolithic** baseline agent (Scenario 1) where the entire catalog is re-evaluated on every turn.
*   **[agent-nexus/caching_app/agent.py](file:///Users/karticn/tokenomics/agent-nexus/caching_app/agent.py)**: Configures the **Context Caching** agent (Scenario 2) with explicit `ContextCacheConfig`.
*   **[agent-nexus/compaction_app/agent.py](file:///Users/karticn/tokenomics/agent-nexus/compaction_app/agent.py)**: Configures the **History Compaction** agent (Scenario 3) with `EventsCompactionConfig` to summarize sliding windows.
*   **[agent-nexus/skills_app/agent.py](file:///Users/karticn/tokenomics/agent-nexus/skills_app/agent.py)**: Configures the **Modular Skills** agent (Scenario 4) utilizing dynamic discovery and on-demand activation.
*   **[agent-nexus/skills/](file:///Users/karticn/tokenomics/agent-nexus/skills/)**: Skill registry containing `SKILL.md` files (frontmatter + instructions) for each city based on the `agentskills.io` standard.

---

## 🚀 Running the Sandbox Locally

### Step 1: Initialize the Environment & Secrets
Make sure you have authenticated your Google Cloud SDK:
```bash
gcloud auth application-default login
```

Verify that **[.env](file:///Users/karticn/tokenomics/.env)** is configured with the correct Google Cloud Project and target model ID (e.g. `publishers/google/models/gemini-3.1-pro-preview`).

### Step 2: Launch the Servers

1. **Start the Dashboard Server (Port 8000):**
   ```bash
   ./run.sh
   ```
2. **Start the ADK Playground Server (Port 8080):**
   ```bash
   cd agent-nexus
   adk web . --host 127.0.0.1 --port 8080 --allow_origins '*' --reload_agents
   ```

### Step 3: Run queries and view results
Send queries to any app naming scenario using the `agents-cli`:
```bash
# Naive App query
agents-cli run --url http://127.0.0.1:8080 --mode adk --app-name naive_app "Hi, Tokyo?"

# Caching App query
agents-cli run --url http://127.0.0.1:8080 --mode adk --app-name caching_app "What hotels do you recommend there?"

# Skills App query (dynamic activation)
agents-cli run --url http://127.0.0.1:8080 --mode adk --app-name skills_app "What hotels and packing tips do you recommend for London?"
```

Now open **http://localhost:8000** in your browser to inspect the comparison metrics!
