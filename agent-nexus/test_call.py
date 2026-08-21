import asyncio
import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models import Gemini
from google.genai import types

# Set Vertex AI env vars
os.environ["GOOGLE_CLOUD_PROJECT"] = "vertexai-demo-ltfpzhaw"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

async def after_model_cb(callback_context, llm_response):
    usage = llm_response.usage_metadata
    if usage:
        print(f"[METRICS] model={llm_response.model_version} input={usage.prompt_token_count} cached={usage.cached_content_token_count} output={usage.candidates_token_count}")
    return None

agent = Agent(
    name="test_agent",
    model=Gemini(model="publishers/google/models/gemini-3.5-flash"),
    instruction="You are a helpful assistant.",
    after_model_callback=after_model_cb
)

async def main():
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="s1")
    runner = Runner(agent=agent, app_name="app", session_service=session_service)
    
    print("Running turn 1...")
    async for event in runner.run_async(
        user_id="user", session_id="s1",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text="Hi, who are you?")]),
    ):
        if event.is_final_response():
            print("Response:", event.content.parts[0].text)

if __name__ == "__main__":
    asyncio.run(main())
