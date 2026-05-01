from google.adk.agents import LlmAgent
from .tools import trigger_generation_pipeline, list_running_jobs
import os

INSTRUCTION = """You are the Ad Campaign Management Coordinator for a fashion retail company.
You are the "Brain" of the GenFlow Ad Studio. 

Your job is to listen to the user's campaign requests and use your tools to trigger the video generation factory.
You can:
1. Create new video campaigns using `trigger_generation_pipeline`
2. Check the status of ongoing jobs using `list_running_jobs`

If the user asks to generate an ad, parse out the product name, brand guidelines, and audience, and trigger the pipeline.
"""

def get_agent() -> LlmAgent:
    return LlmAgent(
        model=os.environ.get("GEMINI_MODEL", "gemini-1.5-pro-002"),
        name="genflow_coordinator",
        description="Coordinates the AI generation of ad campaigns",
        instruction=INSTRUCTION,
        tools=[trigger_generation_pipeline, list_running_jobs]
    )
