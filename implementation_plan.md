# Implementation Plan: Agent Nexus Token Control Tower Demo

Build a premium, highly interactive single-page web application dashboard (**"Agent Nexus: Token Control Tower"**) inside the `/Users/karticn/tokenomics` directory. This web app will visually demonstrate Google Cloud's 5-Layer AI Token Optimization Framework, incorporating Apigee AI Gateway policies, Vertex AI Context Caching, and the Antigravity Harness.

---

## 🎨 Design & Aesthetics System
Following the web development guidelines, we will implement a state-of-the-art developer dashboard with the following specifications:
* **Color Palette:** HSL-tailored premium dark mode:
  * Background: Slate/Charcoal dark HSL (`hsl(222, 47%, 11%)`)
  * Accents: Cobalt Blue (`hsl(217, 91%, 60%)`), Emerald Green (`hsl(142, 71%, 45%)`), Sunset Amber (`hsl(35, 92%, 50%)`), and Rose Red (`hsl(346, 84%, 61%)`)
  * Surface Panels: Translucent glassmorphism (`backdrop-filter: blur(12px)`) with thin borders.
* **Typography:** Google Fonts ("Outfit" or "Inter") for a modern, high-tech interface.
* **Micro-Animations:** Smooth HSL transitions on hover, floating glow effects for routing steps, and pulsing nodes for network queues.

---

## 🏗️ Proposed Folder Structure
We will create a clean, single-page application structure to ensure speed, ease of running, and no dependency friction:

* **[NEW]** `/Users/karticn/tokenomics/index.html` - Semantic HTML5 containing the application shell, layout grids, and dashboard tabs.
* **[NEW]** `/Users/karticn/tokenomics/styles.css` - Custom styling using CSS variables for theme tokens, utility classes, and glassmorphism layouts.
* **[NEW]** `/Users/karticn/tokenomics/app.js` - Client-side state engine handling the calculations, timezone transformations, interactive animations, and loop simulations.
* **[NEW]** `/Users/karticn/tokenomics/run.sh` - Simple helper script to boot a Python static file server and expose the URL.

---

## 💡 Proposed Changes & Components

### 1. Main Application Shell (`index.html`)
* A header containing the **"Agent Nexus"** framework branding, an active ROI savings card, and tab selection buttons for the 5 layers (L1 to L5).
* A responsive split-pane layout:
  * Left Panel: Interactive controls (sliders, checkboxes, toggles).
  * Right Panel: High-fidelity visual feedback (charts, animated flows, code playground).

---

### 2. Layer-by-Layer Interactivity Details

#### 🌐 Layer 1: Infrastructure (Traffic & Capacity Simulator)
* **Controls:** Sliders to adjust daily token workload size (TPM) and timezone selector.
* **Visuals:** An interactive canvas/SVG chart plotting a 24h traffic curve. Overlay buttons show how **Provisioned Throughput (PT)** covers the base, while standard PayGo and **Deferred Agents** (at 50% discount) handle the rest.
* **Timezone Calculator:** Select JAPAC working hours and see them dynamically mapped to Pacific off-peak hours (3 PM - 9 PM PST), changing the cost color code to show instant discounts.

#### 🔀 Layer 2: Model Choice (Apigee Dynamic Routing & Architectural Toggle)
* **Controls:** 
  * Toggle between **Managed Agent Mode** (Scenario 1) and **Client-Side Model Mode** (Scenario 2).
  * Select routing mechanism (Rule-based, LLM-based, or Semantic).
* **Visuals:**
  * Animated sequence diagram showing Apigee gateway intercepting a user prompt, evaluating it, and splitting/routing it to Gemini 3.5 Flash-Lite (formatting), Gemini 3.5 Flash (classification), or Gemini 3.1 Pro (complex logic).
  - Code sandbox displaying python genai SDK snippets matching the selected mode.

#### 💾 Layer 3: Context Optimization (Precision Context Design)
* **Controls:** Panel of checkboxes for 5 optimization strategies: Prompt Caching, Sliding Window, Memory Distillation, Clean Serialization, and Semantic Chunking.
* **Visuals:** A token count bar chart. Toggling checkboxes runs a mock compression animation, showing the token volume shrinking from 500k tokens down to 8k tokens and showing corresponding cost savings.

#### ⚙️ Layer 4: Harness (Antigravity & Extensions)
* **Controls:** Selector for integration extensions (Skills, Hooks, Commands, Plugins, MCP).
* **Visuals:** A comparison table showing the token footprint. Shows how utilizing modular **Skills (30-50 tokens)** instead of monolithic prompt descriptions prevents system-prompt bloat and decouples logic execution.

#### 🛡️ Layer 5: Governance (Apigee Cost Control Tower)
* **Controls:** "Run Simulation" button.
* **Visuals:** Shows a live log stream of an agent execution running into an infinite error-retry loop. Shows Apigee gateway **PromptTokenLimit policy** detecting rate abuse and throttling the call, followed by a simulated **LLMTokenQuota policy** modal asking for human-in-the-loop spend approval.

---

## 🧪 Verification Plan

### Automated Verification
* Run a clean HTML5 and CSS validator command locally (e.g. using standard python/node test frameworks or linters if present).

### Manual Verification
* Execute `run.sh` to boot the web application.
* Browse the app console and verify:
  1. All 5 tabs function and render correctly.
  2. Timezone picker shifts the off-peak highlight window accurately.
  3. Toggle switches update the dynamic code snippet blocks.
  4. Real-time calculator responds to checkboxes and sliders instantly.
