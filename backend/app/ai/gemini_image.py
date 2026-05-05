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

# Gemini API paid tier 1 allows 5 RPM for Imagen 4 Ultra.
# With 3 concurrent avatar variants we stay well under that.
# Add a small stagger (2s between task starts) as a precaution.
_STAGGER_SECS = 2.0


class GeminiImageService:
    def __init__(self, client: genai.Client, settings: Settings):
        self.client = client
        self.settings = settings

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
        use_model = model or self.settings.image_model

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
                ),
            ),
        )

        for part in response.candidates[0].content.parts:
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
        """Generate avatar variants with a small stagger to respect RPM quota.

        Gemini API Imagen 4 Ultra allows 5 RPM (paid tier 1).
        We stagger task starts by 2s so bursts stay comfortably within limit.
        """
        async def _staggered(idx: int) -> bytes:
            if idx > 0:
                await asyncio.sleep(idx * _STAGGER_SECS)
            return await self._generate_single_image(
                prompt, reference_bytes,
                aspect_ratio=aspect_ratio, image_size=image_size,
            )

        tasks = [_staggered(i) for i in range(num_variants)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        images: list[bytes] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Avatar variant %d failed: %s", i, result)
            else:
                images.append(result)

        if not images:
            raise ValueError("All avatar generation attempts failed")

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
        use_model = image_model or self.settings.image_model

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
                ),
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data

        raise ValueError("No image data in storyboard response")
