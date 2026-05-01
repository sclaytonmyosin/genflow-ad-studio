import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.genai.types import Content, Part

try:
    from langfuse import get_client, observe, propagate_attributes
except ImportError:  # pragma: no cover - langfuse optional at runtime
    from contextlib import contextmanager

    def observe(*_args, **_kwargs):  # type: ignore[no-redef]
        def _decorator(fn):
            return fn
        return _decorator if not _args or callable(_args[0]) is False else _args[0]

    def get_client():  # type: ignore[no-redef]
        return None

    @contextmanager  # type: ignore[no-redef]
    def propagate_attributes(**_kwargs):
        yield

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Lazy globals — initialized on first request so Doppler env vars are available
_runner = None
_session_service = None

def _get_runner():
    """Lazily initialize the ADK runner so env vars from Doppler are available."""
    global _runner, _session_service
    if _runner is not None:
        return _runner

    # Ensure GOOGLE_CLOUD_PROJECT is set before any google-auth calls
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id:
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from app.agents.coordinator import get_agent

    agent = get_agent()
    _session_service = InMemorySessionService()
    _runner = Runner(
        app_name="myosin-creative-studio",
        agent=agent,
        session_service=_session_service,
        auto_create_session=True,
    )
    return _runner


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    steps: list[str] = []


@router.post("")
@observe(name="myosin.brain.chat")
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    try:
        runner = _get_runner()

        user_id = "default_user"
        session_id = "default_session"

        new_message = Content(
            role="user",
            parts=[Part.from_text(text=request.message)]
        )

        response_text = ""
        steps: list[str] = []

        with propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=["agent", "coordinator"],
        ):
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
            ):
                content = getattr(event, "content", None)
                if content is None:
                    continue
                for part in getattr(content, "parts", None) or []:
                    text = getattr(part, "text", None)
                    if text:
                        response_text += text
                    fn_call = getattr(part, "function_call", None)
                    if fn_call is not None:
                        name = getattr(fn_call, "name", "tool")
                        steps.append(f"Calling tool: {name}")

        lf = get_client()
        if lf is not None:
            lf.update_current_span(
                input={"message": request.message},
                output={"response": response_text, "steps": steps},
            )

        return ChatResponse(response=response_text or "No response", steps=steps)

    except Exception as e:
        import traceback
        traceback.print_exc()
        lf = get_client()
        if lf is not None:
            lf.update_current_span(level="ERROR", status_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))
