from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from app.agents.coordinator import get_agent

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Instantiate the runner globally so it retains memory across requests
agent = get_agent()
session_service = InMemorySessionService()
runner = Runner(
    app_name="genflow", 
    agent=agent, 
    session_service=session_service,
    auto_create_session=True
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    steps: list[str] = []

@router.post("")
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    try:
        user_id = "default_user"
        session_id = "default_session"
            
        # Convert string to google.genai.types.Content
        new_message = Content(
            role="user",
            parts=[Part.from_text(text=request.message)]
        )
        
        messages = []
        # run_async requires keyword arguments
        response_text = ""
        steps = []
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            if hasattr(event, "message") and event.message and hasattr(event.message, "parts"):
                for part in event.message.parts:
                    if part.text:
                        response_text += part.text
            elif hasattr(event, "tool_call"):
                steps.append(f"Calling tool: {event.tool_call}")

        return ChatResponse(response=response_text or "No response", steps=steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
