# Agent Nexus: Live Playground Tokenomics Dashboard
*This dashboard tracks token consumption in real-time as you chat with the four scenario apps in the playground.*

## 📊 Live Scenario Comparison Table
*(The row representing the active app you just queried is highlighted below)*

| Scenario | Turns | Input (Fresh) | Input (Cached) | Output | Est. Cost | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. Naive Monolithic (Pro) | 4 | 26,741 | 16,234 | 770 | $0.09948 | Idle ⚪ |
| 2. Context Caching (Pro) | 3 | 23,224 | 8,117 | 1,746 | $0.06902 | Idle ⚪ |
| 3. History Compaction (Pro) | 3 | 23,233 | 8,117 | 2,186 | $0.07432 | Idle ⚪ |
| 4. Modular Skills (Pro) | 3 | 11,880 | 0 | 1,590 | $0.06428 | **ACTIVE 🟢** |

---

## 💡 Live Presentation Talking Points
* **Context Caching:** Enabling caching reduced cumulative cost from `$0.09948` to `$0.06902` (**30.6% savings**). Observe how the Cached Input count increases after your first turn!
* **Modular Skills:** Shifting context details to the `activate_skill` tool instead of stuffing it in instructions cut costs by **35.4%**! The input footprint remained tiny on every turn.

*Report updated at: 2026-08-31 13:41:59*
