#!/usr/bin/env python3
"""Smoke test: end-to-end check that the GenFlow coordinator agent can
take a user message and produce a response from the configured LLM.

Run with secrets injected (Doppler in dev/prd, .env locally):

    make smoke-agent
    # or:
    cd backend && doppler run -- .venv/bin/python ../scripts/smoke_agent.py

Exits 0 on success, 1 on any failure. Designed for CI and pre-deploy gates.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

from app.utils import bootstrap  # noqa: E402,F401  -- materialize ADC + observability
from app.agents.coordinator import get_agent  # noqa: E402

from google.adk import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai.types import Content, Part  # noqa: E402

try:
    from langfuse import get_client, observe, propagate_attributes
except ImportError:  # pragma: no cover - langfuse optional
    from contextlib import contextmanager

    def observe(*_args, **_kwargs):  # type: ignore[no-redef]
        def _decorator(fn):
            return fn

        if _args and callable(_args[0]):
            return _args[0]
        return _decorator

    def get_client():  # type: ignore[no-redef]
        return None

    @contextmanager  # type: ignore[no-redef]
    def propagate_attributes(**_kwargs):
        yield


PROMPT = "Reply with the single word: PONG"
TIMEOUT_S = 30


@observe(name="genflow.smoke")
async def run_once() -> str:
    runner = Runner(
        app_name="genflow-smoke",
        agent=get_agent(),
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )
    msg = Content(role="user", parts=[Part.from_text(text=PROMPT)])
    chunks: list[str] = []
    with propagate_attributes(
        user_id="smoke",
        session_id="smoke",
        tags=["smoke", "agent"],
    ):
        async for event in runner.run_async(
            user_id="smoke", session_id="smoke", new_message=msg
        ):
            content = getattr(event, "content", None)
            if content is None:
                continue
            for part in getattr(content, "parts", None) or []:
                text = getattr(part, "text", None)
                if text:
                    chunks.append(text)
    response = " ".join(chunks).strip()

    lf = get_client()
    if lf is not None:
        lf.update_current_span(input={"prompt": PROMPT}, output={"response": response})
    return response


def main() -> int:
    try:
        reply = asyncio.run(asyncio.wait_for(run_once(), timeout=TIMEOUT_S))
    except asyncio.TimeoutError:
        print(f"FAIL: agent did not respond within {TIMEOUT_S}s", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    lf = get_client()
    if lf is not None:
        lf.flush()

    if not reply:
        print("FAIL: agent returned an empty response", file=sys.stderr)
        return 1
    print(f"PASS: agent responded ({len(reply)} chars)")
    print(f"  prompt: {PROMPT}")
    print(f"  reply : {reply[:200]}{'…' if len(reply) > 200 else ''}")
    if lf is not None and lf.auth_check():
        print("  trace : sent to Langfuse (check dashboard)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
