"""
gemini_image.py
───────────────
Image generation service using the **Gemini API** endpoint (not Vertex AI).

Why separate from the Vertex AI client?
  • Vertex AI Imagen 4.0 Ultra quota: ~1 RPM (hard to increase without support ticket)
  • Gemini API Imagen 4.0 Ultra quota: 5 RPM (paid tier 1) — immediately available
  • Veo video generation stays on Vertex AI (not available on Gemini API)

The client passed in here must be created with:
    genai.Client(api_key=settings.gemini_api_key)   # vertexai=False
"""
import asyncio
import logging

from google import genai
from google.genai import types
from google.genai.types import PersonGeneration

from app.ai.retry import async_retry
from app.config import Settings

logger = logging.getLogger(__name__)

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

# Avatar variants are generated sequentially with _VARIANT_GAP_SECS between calls.
# Gemini **Developer API** image model (Vertex-only imagen-3 IDs hit aiplatform RPM).
_DEFAULT_DEV_IMAGE_MODEL = "imagen-4.0-ultra-generate-001"

# Serialize variant requests so we stay under image RPM (parallel bursts were hammering quota).
_VARIANT_GAP_SECS = 4.0


class GeminiImageService:
    def __init__(self, client: genai.Client, settings: Settings):
        self.client = client
        self.settings = settings

    def _normalize_dev_image_model(self, model: str | None) -> str:
        """Map Vertex / Imagen-3 style IDs to a Gemini API Imagen 4 id."""
        raw = (model or self.settings.image_model or _DEFAULT_DEV_IMAGE_MODEL).strip()
        lower = raw.lower()
        if "imagen-3" in lower or "imagegeneration" in lower:
            logger.warning(
                "Remapping IMAGE_MODEL %r to %r (Imagen 3 / legacy IDs use Vertex quotas)",
                raw,
                _DEFAULT_DEV_IMAGE_MODEL,
            )
            return _DEFAULT_DEV_IMAGE_MODEL
        return raw

    @async_retry(retries=3)
    async def _generate_single_image(
        self,
        prompt: str,
        reference_bytes: bytes | None = None,
        aspect_ratio: str = "9:16",
        image_size: str = "2K",
        model: str | None = None,
    ) -> bytes:
        """Generate a single image and return raw bytes."""
        use_model = self._normalize_dev_image_model(model)

        if reference_bytes:
            ref_part = types.Part.from_bytes(
                data=reference_bytes, mime_type="image/png"
            )
            text_part = types.Part.from_text(text=prompt)
            contents = [ref_part, text_part]
        else:
            contents = prompt

        response = await self.client.aio.models.generate_content(
            model=use_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=ALL_SAFETY_OFF,
                temperature=1.0,
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                    # Required for presenters / human avatars; default blocks people.
                    person_generation=PersonGeneration.ALLOW_ADULT,
                ),
            ),
        )

        if not response.candidates:
            fb = getattr(response, "prompt_feedback", None)
            raise ValueError(f"No response candidates (image may be blocked). prompt_feedback={fb}")

        cand = response.candidates[0]
        parts = cand.content.parts if cand.content else []
        for part in parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data

        raise ValueError("No image data in response")

    async def generate_avatar(
        self,
        prompt: str,
        num_variants: int = 4,
        reference_bytes: bytes | None = None,
        aspect_ratio: str = "9:16",
        image_size: str = "2K",
    ) -> list[bytes]:
        """Generate avatar variants one-by-one with a gap between requests (RPM)."""
        images: list[bytes] = []
        errors: list[str] = []
        for i in range(num_variants):
            if i > 0:
                await asyncio.sleep(_VARIANT_GAP_SECS)
            try:
                img = await self._generate_single_image(
                    prompt,
                    reference_bytes,
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                )
                images.append(img)
            except Exception as e:
                logger.error("Avatar variant %d failed: %s", i, e)
                errors.append(f"variant {i}: {e}")

        if not images:
            detail = "; ".join(errors[:4]) if errors else "unknown"
            raise ValueError(f"All avatar generation attempts failed ({detail})")

        return images

    @async_retry(retries=3)
    async def generate_storyboard_image(
        self,
        prompt: str,
        avatar_bytes: bytes,
        product_bytes: bytes,
        image_model: str | None = None,
        aspect_ratio: str = "9:16",
        image_size: str = "2K",
    ) -> bytes:
        """Generate a storyboard image with avatar and product reference images."""
        use_model = self._normalize_dev_image_model(image_model)

        avatar_part = types.Part.from_bytes(data=avatar_bytes, mime_type="image/png")
        product_part = types.Part.from_bytes(data=product_bytes, mime_type="image/png")
        text_part = types.Part.from_text(text=prompt)

        response = await self.client.aio.models.generate_content(
            model=use_model,
            contents=[avatar_part, product_part, text_part],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=ALL_SAFETY_OFF,
                temperature=1.0,
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                    person_generation=PersonGeneration.ALLOW_ADULT,
                ),
            ),
        )

        if not response.candidates:
            fb = getattr(response, "prompt_feedback", None)
            raise ValueError(f"No storyboard candidates. prompt_feedback={fb}")

        cand = response.candidates[0]
        parts = cand.content.parts if cand.content else []
        for part in parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data

        raise ValueError("No image data in storyboard response")
