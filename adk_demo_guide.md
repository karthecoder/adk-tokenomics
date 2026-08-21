# Demo Guide: CLI ADK Tokenomics Showcase

If you want to present the real, programmatic power of the **Agent Development Kit (ADK)** and tokenomics directly from your terminal (bypassing the web UI), follow this guide.

---

## 🛠️ Prep: Initialize the Environment

Open your terminal and navigate to the project directory:
```bash
cd /Users/karticn/tokenomics/agent-nexus
```

Ensure your Vertex AI authentication variables are active in your session:
```bash
export GOOGLE_CLOUD_PROJECT="vertexai-demo-ltfpzhaw"
export GOOGLE_CLOUD_LOCATION="global"
export GOOGLE_GENAI_USE_VERTEXAI="True"
```

---

## 🎙️ Step-by-Step Presentation Script

### Step 1: Run the Full Benchmark
To show the side-by-side ledger comparing all four token configurations immediately, execute the master showcase script:
```bash
python3 run_adk_showcase.py
```

#### 💡 Key Talking Points:
* **The Problem:** Point to **Naive Monolithic (Version 1)**. In a naive setup, every turn sends the massive database schema (6,000+ tokens) over the wire, causing linear input token growth ($0.03213 total cost).
* **The Caching Solution:** Point to **Context Caching (Version 2)**. The prompt schema is stored in memory by Vertex AI. On Turn 1, input tokens are read fresh. On Turns 2 & 3, the input cache hits are read at a **90% cost discount**, reducing TCO to $0.02489 (a **22.5% savings**).
* **The Routing Solution:** Point to **Hybrid Routing (Version 4)**. Instead of using Gemini Pro for everything, we route the initial schema lookups to **Gemini 3.5 Flash Lite** (extremely cheap) and only delegate the final compilation to Pro. Cost drops to **$0.00790** (a **75% savings**!).

---

## 🔬 Step 2: Showcase Individual Runs Live

You can trigger specific configurations to run live and stream the ADK event traces to your console.

### 1. Show the Naive vs. Cache comparison:
Run the naive monolithic agent:
```bash
python3 run_adk_showcase.py naive
```
*Note: Observe how the input tokens remain fully fresh on every single turn.*

Run the cached agent:
```bash
python3 run_adk_showcase.py caching
```
*Note: Highlight the `[ADK Trace] cached=...` console updates showing that the cached token volume matches the schema size on subsequent turns.*

### 2. Show Dynamic Multi-Agent Routing:
Run the dynamic routing stack:
```bash
python3 run_adk_showcase.py routing
```
*Note: Point out the two sequential model executions: Gemini 3.5 Flash Lite prints its trace first, immediately followed by the Gemini 3.1 Pro reasoning pass.*
