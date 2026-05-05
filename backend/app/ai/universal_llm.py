"""
universal_llm.py
─────────────────
A unified LLM interface routing text/vision tasks to the right provider:

  • gemini-*          → Google Vertex AI (google.genai)
  • anthropic/*       → Anthropic directly (via openai-compat) or OpenRouter
  • openai/*          → OpenAI directly
  • x-ai/*            → xAI (Grok) via OpenAI-compatible endpoint
  • mistralai/*       → Mistral directly
  • moonshot/*        → Kimi/Moonshot directly
  • everything else   → OpenRouter (catch-all)

Image + video generation always stay on Vertex AI (Imagen / Veo).
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from app.ai.prompts import (
    PROMPT_REWRITE_TEMPLATE,
    SCRIPT_SYSTEM_INSTRUCTION,
    SCRIPT_USER_PROMPT_TEMPLATE,
    STORYBOARD_QC_SYSTEM_INSTRUCTION,
    STORYBOARD_QC_USER_PROMPT,
    VIDEO_QC_SYSTEM_INSTRUCTION,
    VIDEO_QC_USER_PROMPT,
    build_narrative_arc,
)
from app.ai.retry import async_retry
from app.config import Settings
from app.utils.json_parser import parse_json_response

logger = logging.getLogger(__name__)

# ── Provider routing ──────────────────────────────────────────────────────────

_GOOGLE_PREFIXES = ("gemini-", "publishers/google/")

def _provider_for(model: str) -> str:
    if any(model.startswith(p) for p in _GOOGLE_PREFIXES):
        return "google"
    if model.startswith("anthropic/") or model.startswith("claude-"):
        return "anthropic"
    if model.startswith("openai/") or model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
        return "openai"
    if model.startswith("x-ai/") or model.startswith("grok-"):
        return "xai"
    if model.startswith("mistralai/") or model.startswith("mistral-") or model.startswith("codestral"):
        return "mistral"
    if model.startswith("moonshot/") or model.startswith("kimi-") or "kimi" in model:
        return "kimi"
    # Default: route through OpenRouter (handles meta-llama, bytedance/doubao, etc.)
    return "openrouter"


def _strip_provider_prefix(model: str) -> str:
    """Strip provider namespace prefix for direct API calls."""
    for prefix in ("anthropic/", "openai/", "x-ai/", "mistralai/", "moonshot/"):
        if model.startswith(prefix):
            return model[len(prefix):]
    return model


def _image_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


# ── Service ───────────────────────────────────────────────────────────────────

class UniversalLLMService:
    """
    Drop-in replacement for GeminiService.
    Routes each call to the appropriate provider based on the model ID.
    """

    def __init__(self, genai_client, settings: Settings):
        from google.genai import types as genai_types
        self._genai_client = genai_client
        self._settings = settings
        self._genai_types = genai_types
        self._clients: dict = {}  # provider → AsyncOpenAI-compatible client

    def _get_client(self, provider: str):
        """Get (or lazily create) the async client for a provider."""
        if provider in self._clients:
            return self._clients[provider]

        from openai import AsyncOpenAI

        s = self._settings
        if provider == "openrouter":
            if not s.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY not set in Doppler genflow/prd")
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=s.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://myosin.ai",
                    "X-Title": "Myosin Creative Studio",
                },
            )
        elif provider == "anthropic":
            # Anthropic is OpenAI-compatible via their messages endpoint
            key = s.anthropic_api_key or s.openrouter_api_key
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not set in Doppler genflow/prd")
            # Route via OpenRouter for simplicity (avoids anthropic SDK dep)
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=s.openrouter_api_key or s.anthropic_api_key,
                default_headers={
                    "HTTP-Referer": "https://myosin.ai",
                    "X-Title": "Myosin Creative Studio",
                },
            )
        elif provider == "openai":
            if not s.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set in Doppler genflow/prd")
            client = AsyncOpenAI(api_key=s.openai_api_key)
        elif provider == "xai":
            if not s.xai_api_key:
                raise ValueError("XAI_API_KEY not set in Doppler genflow/prd")
            client = AsyncOpenAI(
                base_url="https://api.x.ai/v1",
                api_key=s.xai_api_key,
            )
        elif provider == "mistral":
            if not s.mistral_api_key:
                raise ValueError("MISTRAL_API_KEY not set in Doppler genflow/prd")
            client = AsyncOpenAI(
                base_url="https://api.mistral.ai/v1",
                api_key=s.mistral_api_key,
            )
        elif provider == "kimi":
            if not s.kimi_api_key:
                raise ValueError("KIMI_API_KEY not set in Doppler genflow/prd")
            client = AsyncOpenAI(
                base_url="https://api.moonshot.cn/v1",
                api_key=s.kimi_api_key,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self._clients[provider] = client
        return client

    # ── OpenAI-compatible call (non-Google) ───────────────────────────────────

    async def _openai_generate(
        self,
        model: str,
        system: str,
        messages: list[dict],
        temperature: float = 1.0,
        json_mode: bool = True,
    ) -> str:
        provider = _provider_for(model)
        client = self._get_client(provider)

        # For OpenRouter-routed models keep the full model id (e.g. anthropic/claude-opus-4-5)
        # For direct providers strip the prefix
        if provider not in ("openrouter", "anthropic"):
            model_id = _strip_provider_prefix(model)
        else:
            model_id = model

        sys_msgs = [{"role": "system", "content": system}] if system else []
        kwargs: dict = dict(
            model=model_id,
            messages=sys_msgs + messages,
            temperature=temperature,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    # ── Google Vertex AI call ─────────────────────────────────────────────────

    async def _google_generate(
        self,
        model: str,
        contents,
        system_instruction: str | None = None,
        response_mime_type: str = "application/json",
        temperature: float = 1.0,
    ) -> str:
        types = self._genai_types
        ALL_SAFETY_OFF = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.OFF,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
        config = types.GenerateContentConfig(
            safety_settings=ALL_SAFETY_OFF,
            temperature=temperature,
        )
        if system_instruction:
            config.system_instruction = system_instruction
        if response_mime_type:
            config.response_mime_type = response_mime_type

        response = await self._genai_client.aio.models.generate_content(
            model=model, contents=contents, config=config
        )
        return response.text

    # ── Public methods (GeminiService-compatible interface) ───────────────────

    @async_retry(retries=3)
    async def generate_script(
        self,
        product_name: str,
        specs: str,
        image_bytes: bytes,
        scene_count: int = 3,
        target_duration: int = 30,
        ad_tone: str = "energetic",
        model_id: Optional[str] = None,
        max_words: int = 25,
        custom_instructions: str = "",
    ) -> dict:
        model = model_id or self._settings.gemini_model

        user_prompt = SCRIPT_USER_PROMPT_TEMPLATE.format(
            product_name=product_name,
            specs=specs,
            scene_count=scene_count,
            target_duration=target_duration,
            narrative_arc=build_narrative_arc(scene_count, target_duration),
            ad_tone=ad_tone,
            max_words=max_words,
        )
        if custom_instructions:
            user_prompt += f"\n\nADDITIONAL CREATIVE DIRECTION FROM CLIENT:\n{custom_instructions}"

        provider = _provider_for(model)
        logger.info("generate_script: model=%s provider=%s", model, provider)

        if provider == "google":
            types = self._genai_types
            contents = [
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                types.Part.from_text(text=user_prompt),
            ]
            raw = await self._google_generate(
                model=model, contents=contents,
                system_instruction=SCRIPT_SYSTEM_INSTRUCTION, temperature=1.0,
            )
        else:
            data_url = _image_to_data_url(image_bytes)
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": user_prompt},
                ],
            }]
            raw = await self._openai_generate(
                model=model, system=SCRIPT_SYSTEM_INSTRUCTION,
                messages=messages, temperature=1.0, json_mode=True,
            )

        return parse_json_response(raw)

    @async_retry(retries=3)
    async def analyze_product_image(self, image_bytes: bytes) -> dict:
        """Always uses Gemini flash — fast image-to-JSON extraction."""
        model = self._settings.gemini_flash_model
        prompt = (
            "Analyze this product image and extract the following information. "
            "Return ONLY valid JSON with no additional text.\n\n"
            '{"product_name": "The product name", '
            '"specifications": "Key specifications formatted as key: value lines"}'
        )
        types = self._genai_types
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            types.Part.from_text(text=prompt),
        ]
        raw = await self._google_generate(
            model=model, contents=contents,
            response_mime_type="application/json", temperature=0.5,
        )
        return parse_json_response(raw)

    @async_retry(retries=3)
    async def qc_storyboard(
        self,
        avatar_bytes: bytes,
        product_bytes: bytes,
        storyboard_bytes: bytes,
    ) -> dict:
        """Always uses Gemini flash — multimodal vision + structured JSON."""
        model = self._settings.gemini_flash_model
        types = self._genai_types
        contents = [
            types.Part.from_bytes(data=avatar_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=product_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=storyboard_bytes, mime_type="image/png"),
            types.Part.from_text(text=STORYBOARD_QC_USER_PROMPT),
        ]
        raw = await self._google_generate(
            model=model, contents=contents,
            system_instruction=STORYBOARD_QC_SYSTEM_INSTRUCTION, temperature=1.0,
        )
        return parse_json_response(raw)

    @async_retry(retries=3)
    async def qc_video(self, video_uri: str, reference_image_uri: str) -> dict:
        """Always uses Gemini — GCS URI access is Google-only."""
        model = self._settings.gemini_flash_model
        types = self._genai_types
        contents = [
            types.Part.from_uri(file_uri=reference_image_uri, mime_type="image/png"),
            types.Part.from_uri(file_uri=video_uri, mime_type="video/mp4"),
            types.Part.from_text(text=VIDEO_QC_USER_PROMPT),
        ]
        raw = await self._google_generate(
            model=model, contents=contents,
            system_instruction=VIDEO_QC_SYSTEM_INSTRUCTION, temperature=1.0,
        )
        return parse_json_response(raw)

    @async_retry(retries=3)
    async def rewrite_prompt(self, original_prompt: str, qc_feedback: str) -> str:
        """Always uses Gemini flash for speed."""
        model = self._settings.gemini_flash_model
        prompt_text = PROMPT_REWRITE_TEMPLATE.format(
            original_prompt=original_prompt, qc_feedback=qc_feedback,
        )
        raw = await self._google_generate(
            model=model, contents=prompt_text,
            system_instruction=None, response_mime_type="", temperature=1.0,
        )
        return raw.strip()
