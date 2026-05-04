"""Genflow integration: wire Apollo's brand_critic into the storyboard QC step.

Drop-in extension for genflow-ad-studio's QC pipeline. After the existing
visual QC scoring, run `brand_critic` against the storyboard's narration /
copy text and add a `brand_fit_score` dimension to the QC report.

If brand_fit_score < client.brand_qc_threshold (default 70), the storyboard
is rejected and regenerated with the brand_critic's rewrite suggestion as
additional prompt context.

Wiring (one-time, in genflow backend):
    # backend/app/services/qc_service.py — at top
    from app.services.brand_qc_integration import score_brand_fit

    # in QCService.score_storyboard(), after existing visual scoring:
    brand_score = await score_brand_fit(
        storyboard=storyboard,
        client_slug=request.client_slug,
        target_score=request.brand_qc_threshold or 70,
    )
    qc_report.brand_fit = brand_score
    if brand_score.get("fit_score", 100) < (request.brand_qc_threshold or 70):
        qc_report.passes = False
        qc_report.regen_hints.append(brand_score.get("rewrite") or "")
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)

# Allow genflow backend to import the brand_critic implementation directly
# from the hermes-agent installation. They live on the same VM.
HERMES_AGENT_PATH = os.environ.get(
    "HERMES_AGENT_PATH", "/home/hermes/hermes-agent"
)
if HERMES_AGENT_PATH not in sys.path:
    sys.path.insert(0, HERMES_AGENT_PATH)


async def score_brand_fit(
    storyboard: Any,
    client_slug: str,
    target_score: int = 70,
) -> dict[str, Any]:
    """Score a storyboard's copy against the client's brand voice.

    `storyboard` is genflow's storyboard object — we extract the visible copy
    (scene narrations, on-screen text, voiceover) and pass to brand_critic.
    """
    if not client_slug:
        logger.info("brand_fit: no client_slug provided, skipping")
        return {"fit_score": None, "skipped": True, "reason": "no client_slug"}

    try:
        from tools.pantheon.brand_critic import brand_critic
    except ImportError as e:
        logger.warning("brand_critic not importable: %s — skipping brand QC", e)
        return {"fit_score": None, "skipped": True, "reason": f"import error: {e}"}

    draft = _extract_storyboard_copy(storyboard)
    if not draft:
        return {"fit_score": None, "skipped": True, "reason": "no copy in storyboard"}

    try:
        # brand_critic is sync (runs an LLM call internally). For an async
        # context, run in default executor so we don't block the event loop.
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: brand_critic(draft=draft, client_slug=client_slug, target_score=target_score),
        )
        return result
    except Exception as e:
        logger.error("brand_critic call failed: %s", e)
        return {"fit_score": None, "skipped": True, "reason": f"critic error: {e}"}


def _extract_storyboard_copy(storyboard: Any) -> str:
    """Pull all visible copy (narration, voiceover, on-screen text) from a
    genflow storyboard object. Defensive — works whether it's a Pydantic
    model, a dict, or an iterable of scenes.
    """
    parts: list[str] = []

    # Pydantic model with .scenes
    scenes = getattr(storyboard, "scenes", None)
    if scenes is None and isinstance(storyboard, dict):
        scenes = storyboard.get("scenes", [])

    if scenes:
        for scene in scenes:
            for field in ("narration", "voiceover", "voice_over", "on_screen_text",
                          "text", "copy", "headline", "subhead", "cta"):
                val = getattr(scene, field, None) if not isinstance(scene, dict) else scene.get(field)
                if val and isinstance(val, str):
                    parts.append(val.strip())

    # Top-level fields some genflow scripts use
    for field in ("script", "headline", "tagline", "cta", "voiceover_full"):
        val = getattr(storyboard, field, None) if not isinstance(storyboard, dict) else storyboard.get(field) if isinstance(storyboard, dict) else None
        if val and isinstance(val, str):
            parts.append(val.strip())

    return "\n\n".join(p for p in parts if p)
