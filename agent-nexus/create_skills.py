import os
import sys

# Inject prompts path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from prompts import get_large_catalog

cities = [
    "Paris", "Tokyo", "London", "Rome", "New York", "Singapore", "Sydney", "Barcelona", "Dubai", "Bangkok",
    "Cairo", "Cape Town", "Rio de Janeiro", "Vancouver", "Amsterdam", "Prague", "Vienna", "Istanbul", "Seoul", "Hong Kong",
    "Munich", "San Francisco", "Chicago", "Boston", "Seattle", "Miami", "Los Angeles", "Honolulu", "Toronto", "Montreal",
    "Stockholm", "Oslo", "Copenhagen", "Zurich", "Geneva", "Athens", "Dublin", "Edinburgh", "Madrid", "Lisbon"
]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(base_dir, "skills")
    os.makedirs(skills_dir, exist_ok=True)
    
    for i, city in enumerate(cities):
        folder_name = f"{city.lower().replace(' ', '-')}-travel"
        city_skills_dir = os.path.join(skills_dir, folder_name)
        os.makedirs(city_skills_dir, exist_ok=True)
        
        skill_md_content = f"""---
name: {folder_name}
description: Access travel recommendations, hotels, guidelines, and tips for {city}. Use when user asks about {city}.
license: Apache-2.0
metadata:
  author: travel-nexus
  version: "1.0"
---
# {city} Travel Skill

## Destination Information
*   **City:** {city}
*   **Country Region:** International Zone {i+1}
*   **About:** A prime world city offering premier cultural, dining, and historic landmarks.

## Recommended Hotels
*   **Grand {city} Resort:** A 5-star premier hotel with world-class dining, spa, and shuttle service.
*   **{city} Heritage Inn:** Boutique hotel located in the historic city center, walking distance to landmarks.
*   **Budget Stay {city}:** Affordable clean lodging with high-speed Wi-Fi, perfect for business travelers.

## Local Rules & Cultural Norms
*   **Tipping:** Service charge is typically included. Standard extra tip of 5-10% is appreciated for exceptional service.
*   **Quiet Hours:** Enforced from 10:00 PM to 7:00 AM daily.
*   **Transport:** Use local metro or verified taxi apps. Avoid unregistered street solicitations.
*   **Safety:** Keep belongings secure in crowded tourist spots.

## Packing Guidelines
*   Bring comfortable walking shoes, weather-appropriate clothing layers, and a local travel adapter.

## Emergency Contact
*   Call **112** or the local visitor support line at **900-555-{i:03d}**.
"""
        with open(os.path.join(city_skills_dir, "SKILL.md"), "w") as f:
            f.write(skill_md_content)
            
    print(f"Successfully generated {len(cities)} skills in: {skills_dir}")

if __name__ == "__main__":
    main()
