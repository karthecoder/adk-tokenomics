# Prompts and instructions configurations for Agent Nexus Travel Planner Apps

def get_large_catalog():
    catalog = "GLOBAL DESTINATION TRAVEL CATALOG\n=================================\n\n"
    cities = [
        "Paris", "Tokyo", "London", "Rome", "New York", "Singapore", "Sydney", "Barcelona", "Dubai", "Bangkok",
        "Cairo", "Cape Town", "Rio de Janeiro", "Vancouver", "Amsterdam", "Prague", "Vienna", "Istanbul", "Seoul", "Hong Kong",
        "Munich", "San Francisco", "Chicago", "Boston", "Seattle", "Miami", "Los Angeles", "Honolulu", "Toronto", "Montreal",
        "Stockholm", "Oslo", "Copenhagen", "Zurich", "Geneva", "Athens", "Dublin", "Edinburgh", "Madrid", "Lisbon"
    ]
    for i, city in enumerate(cities):
        catalog += f"""
Destination City {i+1}: {city}
Country Region: International Zone {i+1}
About: A prime world city offering premier cultural, dining, and historic landmarks.
Recommended Hotels:
  - Grand {city} Resort: A 5-star premier hotel with world-class dining, spa, and shuttle service.
  - {city} Heritage Inn: A boutique hotel located in the historic city center, walking distance to landmarks.
  - Budget Stay {city}: Affordable clean lodging with high-speed Wi-Fi, perfect for business travelers.
Local Rules & Cultural Norms:
  - Tipping: Service charge is typically included. Standard extra tip of 5-10% is appreciated for exceptional service.
  - Quiet Hours: Strictly enforced from 10:00 PM to 7:00 AM daily.
  - Transport: Use local metro or verified taxi apps. Avoid unregistered street solicitations.
  - Safety: Keep belongings secure in crowded tourist spots.
Packing Guidelines:
  - Bring comfortable walking shoes, weather-appropriate clothing layers, and a local travel adapter.
Emergency Contact: Call 112 or local visitor support line at 900-555-{i:03d}.
"""
    return catalog

# Large Travel Catalog (used to demonstrate Prompt Caching token sizes)
CATALOG_TEXT = get_large_catalog()

# Layer 1/2/3 Monolithic Agent Prompt
NAIVE_INSTRUCTION = f"You are a travel planning assistant. Use this destination travel catalog to recommend hotels, activities, and rules. IMPORTANT: You are designed as a generic, white-label travel planner. Do not reveal the name of your underlying backend model or technology provider (e.g. Gemini, Google, Claude, OpenAI) to the user under any circumstances. If asked about your model, architecture, or creators, state that you are a travel planning assistant developed for this service.\n{CATALOG_TEXT}"

# Caching Agent Prompt
CACHING_INSTRUCTION = NAIVE_INSTRUCTION

# History Compaction Agent Prompt
COMPACTION_INSTRUCTION = NAIVE_INSTRUCTION

# Layer 4 Skills Agent Prompt (No context catalog, fetches via tool call)
SKILLS_INSTRUCTION_TEMPLATE = "You are a travel planning assistant. The following skills are available to give you new capabilities and expertise:\n\n{skills_catalog}\n\nWhen a task matches a skill's description, call the activate_skill tool with the skill's name to load its full instructions. Do not guess information. IMPORTANT: You are designed as a generic, white-label travel planner. Do not reveal the name of your underlying backend model or technology provider (e.g. Gemini, Google, Claude, OpenAI) to the user under any circumstances. If asked about your model, architecture, or creators, state that you are a travel planning assistant developed for this service."
