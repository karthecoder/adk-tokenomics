# Travel Planner Presentation Script: Live Playground Demo

Use this step-by-step story during your presentation. It sets up a realistic scenario: **planning a vacation with an AI travel guide** that has access to a massive **6,000-token Global Destination Catalog** (housing hotels, cultural tips, tipping rules, and emergencies for 40 major cities).

---

## 🟥 Scenario 1: `naive_app` (The Costly Baseline)
*This demonstrates what happens when context optimization is ignored.*

1. **Step:** Select **`naive_app`** in the playground.
2. **Action:** Type and send:
   ```text
   What are the tipping guidelines and quiet hours in Paris?
   ```
3. **Show the Webapp Dashboard (port 8000):**
   * *Highlight:* **Input (Fresh)** is ~6,300 tokens. **Input (Cached)** is **0**.
   * *Pitch:* *"Every single question we ask our assistant forces Vertex AI to re-read the entire travel guide from scratch. If a user chats for 10 turns, they are billed for over 60,000 tokens just to look up basic tips."*

---

## 🟩 Scenario 2: `caching_app` (Context Caching)
*This demonstrates the 90% discount on static, heavy prompts.*

1. **Step:** Select **`caching_app`** in the playground and click **New Session**.
2. **Action - Turn 1 (Cache Write):** Type and send:
   ```text
   What are the tipping guidelines and quiet hours in Paris?
   ```
   * *Check Dashboard:* **Input (Cached)** is **0** because this first turn compiled the cache.
3. **Action - Turn 2 (Cache Hit):** Type and send:
   ```text
   What hotels do you recommend there?
   ```
4. **Show the Webapp Dashboard (port 8000):**
   * *Highlight:* **Input (Cached)** jumps to **~6,320 tokens**.
   * *Pitch:* *"Notice Turn 2. Because the massive travel catalog was cached in Vertex AI memory on the first turn, our second turn was billed at a **90% discount** ($0.174/1M tokens instead of $1.74/1M). The total cost remains virtually flat."*

---

## 🟨 Scenario 3: `compaction_app` (History Compaction)
*This demonstrates capping context bloat in long conversations.*

### The Concept to Pitch:
*"As chats grow, history balloons, making each turn increasingly expensive. History Compaction automatically trims or summarizes early turns, keeping the dynamic prompt footprint bounded."*

### Demo Steps:
1. Select **`compaction_app`** in the playground.
2. Click **New Session** to reset the timeline.
3. Send these 6 queries sequentially to trigger compaction (configured with `compaction_interval=4`):
   * **Turn 1:** `Hi, what is the best city to visit in South America?`
   * **Turn 2:** `Why not Rio de Janeiro?`
   * **Turn 3:** `What are the top hotels there?`
   * **Turn 4:** `What are local safety guidelines?`
     * *(At this point, 4 user turns have completed. Compaction triggers in the background to summarize turns 1-3)*
   * **Turn 5:** `Can you recommend quiet hours rules?`
   * **Turn 6:** `What about tipping rules?`

### What to Show on the Live Dashboard (port 8000):
Point out the **"Compaction Drop"** on the metrics graph or BigQuery table:
* **Turns 1 to 4:** You will see the total `prompt_tokens` grow steadily (e.g., from `10,295` to `10,874` tokens) as history accumulates.
* **Turn 5 (Compaction Triggered):** 
  * The total `prompt_tokens` **drops** (e.g., down to `10,555` tokens) because the ADK has summarized the first 3 turns into a single compact paragraph.
  * Note: Because the conversation history changed, you will see `cached_tokens = 0` on Turn 5 as the model builds a fresh cache prefix.
* **Turn 6:** The cache is hit successfully again (`cached_tokens` returns to `~8,060`), but the total prompt size remains lean.

---

## 🟦 Scenario 4: `skills_app` (Modular Tool Retrieval - agentskills.io spec)
*This demonstrates avoiding context bloat entirely by loading capabilities on-demand.*

1. **Step:** Select **`skills_app`** in the playground and click **New Session**.
2. **Action:** Type and send:
   ```text
   What hotels and packing tips do you recommend for Tokyo?
   ```
3. **Watch the Playground UI / CLI Logs:**
   * Notice that the agent matches the request to the `tokyo-travel` skill from its available skills catalog, and executes the **`activate_skill(name="tokyo-travel")`** tool.
   * Under the hood, this dynamically loads the `tokyo-travel/SKILL.md` instruction file into context in a structured XML format.
4. **Show the Webapp Dashboard (port 8000):**
   * *Highlight:* **Input (Fresh)** is extremely low (around **~250 tokens**).
   * *Pitch:* *"Instead of stuffing the massive 6,000-token travel guide into the agent's instructions (or paying caching write overhead), the agent discovers the skills registry on boot and dynamically loads ONLY the necessary instructions for the matching skill on-demand. This reduces TCO by **96%** from turn 1."*
