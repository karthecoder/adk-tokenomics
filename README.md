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

## 📋 Prerequisites

Before running the sandbox, ensure you have the following prerequisites installed and configured:

1. **Python 3.10+** (Tested on Python 3.13).
2. **Google Cloud SDK (`gcloud`)**: Installed and authenticated for Vertex AI and BigQuery access (`gcloud auth application-default login`).
3. **Google Agent Development Kit (ADK)**: `pip install google-adk`
4. **Environment File (`.env`)**: Required configuration file created from template (`cp .env.example .env`).

---

## 🚀 Quickstart & Setup Guide

### Step 1: Environment Setup (`.env` Configuration)

To run the sandbox successfully, create your local `.env` configuration from the provided template:

```bash
cp .env.example .env
```

Edit your **[.env](file:///Users/karticn/tokenomics/.env)** file with your Google Cloud credentials and desired model parameters:

```env
# Agent Nexus Model Configuration
DEMO_MODEL_NAME=publishers/google/models/gemini-3.5-flash
THINKING_BUDGET=4096
MAX_OUTPUT_TOKENS=8192

# GCP & BigQuery Credentials
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional: Anthropic API Key (Required for Claude models)
# ANTHROPIC_API_KEY=your-anthropic-api-key
```

#### Key `.env` Parameters:
| Variable | Description | Example / Allowed Values |
|---|---|---|
| `DEMO_MODEL_NAME` | Active LLM model ID | `publishers/google/models/gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3.7-flash`, `claude-sonnet-5` |
| `THINKING_BUDGET` | Reasoning token budget or effort | `0` (Off), `1024` (Low), `4096` (High), `-1` (Dynamic) |
| `MAX_OUTPUT_TOKENS` | Max output token limit | `1024`, `2048`, `4096`, `8192`, `16384` |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID (Vertex AI & BigQuery enabled) | `your-gcp-project-id` |
| `GOOGLE_CLOUD_LOCATION` | GCP Region | `us-central1` / `global` |

---

### Step 2: Authenticate Google Cloud SDK
Ensure your local environment is authenticated to access Vertex AI and BigQuery:
```bash
gcloud auth application-default login
```

---

### Step 3: Launch Local Servers

1. **Start the Control Tower Dashboard Server (Port 8002):**
   ```bash
   python3 server.py 8002
   ```
2. **Start the ADK Web Playground Server (Port 8082):**
   ```bash
   cd agent-nexus
   adk web . --host 127.0.0.1 --port 8082 --allow_origins '*' --reload_agents
   ```

---

### Step 4: Access Dashboard & Run Queries

1. Open **[http://localhost:8002](http://localhost:8002)** in your browser to view the **Token Control Tower Dashboard**.
2. Click **`💬 Agent Playground`** to interact with agents in real-time or switch to **`📊 Telemetry & Analytics`** to inspect token compounding, cost ledgers, and BigQuery metrics!
3. Alternatively, test queries via the `agents-cli`:
   ```bash
   # Test Naive App (Scenario 1)
   agents-cli run --url http://127.0.0.1:8082 --mode adk --app-name naive_app "Hi, Tokyo?"

   # Test Context Caching App (Scenario 2)
   agents-cli run --url http://127.0.0.1:8082 --mode adk --app-name caching_app "What hotels do you recommend there?"

   # Test Modular Skills App (Scenario 4)
   agents-cli run --url http://127.0.0.1:8082 --mode adk --app-name skills_app "What hotels and packing tips do you recommend for London?"
   ```
