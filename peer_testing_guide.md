# Token Control Tower: Peer Testing & Kickstart Script

Welcome to the **Agent Tokenomics & Context Optimization Sandbox**! 

This guide provides step-by-step sample conversation scripts that you can copy-paste into the **`💬 Agent Playground`** to observe how different context management techniques optimize token consumption and cost.

---

## 🎯 The 4 Agent Scenarios Explained

| Scenario App | Architecture | What It Demonstrates |
|---|---|---|
| **`1. Naive Monolithic`** | Baseline | Evaluates the full city catalog on *every single turn*. Watch input tokens scale linearly! |
| **`2. Context Caching`** | Gemini Implicit Cache | Caches static catalog context in Vertex AI. Input tokens are read at **90% discount** ($0.0375/1M). |
| **`3. History Compaction`** | Sliding Summarization | Automatically prunes/summarizes long history turns, keeping context windows tight and fast. |
| **`4. Modular Skills`** | On-Demand Discovery | Dynamically discovers and loads only the specific city skill needed (`agentskills.io` standard). |

---

## 💬 Sample Multi-Turn Interaction Script

Copy-paste these prompts into the **Agent Playground** (select your app from the top-left dropdown in the chat panel):

### Turn 1: Initial Destination Query
**User Prompt:**
> "Hi! I am planning a 3-day trip to Tokyo next month. Can you recommend top 3 must-visit neighborhoods and budget hotels?"

**Agent Response (Sample):**
> "Hello! Tokyo is an incredible destination. Here are 3 top neighborhoods and budget hotel recommendations:
> 1. **Shinjuku**: Great for nightlife, shopping, and transportation. *Hotel: Tokyu Stay Shinjuku* (~$90/night).
> 2. **Asakusa**: Historic district featuring Senso-ji temple. *Hotel: Kaminarimon Ryokan* (~$75/night).
> 3. **Shibuya**: Famous scramble crossing & trendy cafes. *Hotel: Shibuya Granbell Hotel* (~$110/night)."

---

### Turn 2: Follow-Up & Local Food Advice
**User Prompt:**
> "Awesome! What local dishes or street food should I definitely try while in Shinjuku and Asakusa?"

**Agent Response (Sample):**
> "While exploring Shinjuku and Asakusa, don't miss these local specialties:
> - **Shinjuku (Omoide Yokocho)**: Grilled Yakitori skewers and piping hot Ramen at Memory Lane.
> - **Asakusa (Nakamise Street)**: Ningyo-yaki (sweet bean cakes) and freshly fried Melonpan bread!"

---

### Turn 3: Packing & Weather Tip
**User Prompt:**
> "What should I pack for Tokyo weather next month, and what is the local currency exchange tip?"

**Agent Response (Sample):**
> "For next month in Tokyo, expect pleasant temperatures (15°C – 22°C):
> - **Packing**: Layered light jacket, comfortable walking shoes, and a compact umbrella.
> - **Currency Tip**: Japan uses the Japanese Yen (JPY). Cash is still widely preferred in smaller shops; withdraw Yen at 7-Eleven ATMs using international debit cards."

---

## 📊 What to Observe in the `📊 Telemetry & Analytics` Tab

After testing the conversation script across different apps:

1. **Compare Naive vs. Context Caching (`caching_app`):**
   - Notice how `Prompt Cache Read Ratio` jumps up to **80% - 90%**!
   - Compare `Accumulated Session Spend`: Caching reduces input costs by **~75% - 85%**.
2. **Compare Naive vs. Modular Skills (`skills_app`):**
   - Notice how `Reasoning & Output Tokens` and `Fresh Input Tokens` drop drastically because only the Tokyo skill instructions were loaded instead of all 40 cities!
3. **Compare Models in the Controls Bar:**
   - Switch active models (**Gemini 3.5 Flash**, **Gemini 3.6 Flash**, **Gemini 3.7 Flash**, **Claude Sonnet 5**) to compare rate cards live on your conversation history!

---

## 🔗 Live Sandbox Link
👉 Share this link with your peers: **[https://token-control-tower-1092829253163.us-central1.run.app](https://token-control-tower-1092829253163.us-central1.run.app)**
