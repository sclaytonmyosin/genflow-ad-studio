from functools import lru_cache

from google import genai
from google.cloud import storage

from app.ai.gemini import GeminiService
from app.ai.universal_llm import UniversalLLMService
from app.ai.gemini_image import GeminiImageService
from app.ai.imagen import ImagenService
from app.ai.veo import VeoService
from app.config import Settings
from app.config import get_settings as _get_settings
from app.db import Database
from app.jobs.events import SSEBroadcaster
from app.jobs.runner import TaskRunner
from app.jobs.store import JobStore
from app.services.avatar_service import AvatarService
from app.services.bulk_service import BulkService
from app.services.input_service import InputService
from app.services.log_service import LogService
from app.services.pipeline_service import PipelineService
from app.services.qc_service import QCService
from app.services.review_service import ReviewService
from app.services.script_service import ScriptService
from app.services.stitch_service import StitchService
from app.services.storyboard_service import StoryboardService
from app.services.video_service import VideoService
from app.storage.gcs import GCSStorage
from app.storage.local import LocalStorage


def get_settings() -> Settings:
    return _get_settings()


@lru_cache
def get_genai_client() -> genai.Client:
    import os
    settings = get_settings()
    # Ensure GOOGLE_CLOUD_PROJECT is set so ADC can resolve the project
    if settings.project_id:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.project_id)
    return genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )


@lru_cache
def get_storage_client() -> storage.Client:
    settings = get_settings()
    return storage.Client(project=settings.project_id)


# ---------------------------------------------------------------------------
# Singletons for job infrastructure
# ---------------------------------------------------------------------------

_database: Database | None = None
_job_store: JobStore | None = None
_broadcaster: SSEBroadcaster | None = None
_task_runner: TaskRunner | None = None
_review_service: ReviewService | None = None
_log_service: LogService | None = None


def get_database() -> Database:
    global _database
    if _database is None:
        _database = Database()
    return _database


def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = JobStore(db=get_database())
    return _job_store


def get_broadcaster() -> SSEBroadcaster:
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = SSEBroadcaster()
    return _broadcaster


def get_task_runner() -> TaskRunner:
    global _task_runner
    if _task_runner is None:
        _task_runner = TaskRunner()
    return _task_runner


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

@lru_cache
def get_local_storage() -> LocalStorage:
    settings = get_settings()
    return LocalStorage(base_dir=settings.output_dir)


@lru_cache
def get_gcs_storage() -> GCSStorage:
    settings = get_settings()
    return GCSStorage(
        bucket_name=settings.gcs_bucket_name,
        project_id=settings.project_id,
    )


# ---------------------------------------------------------------------------
# AI services
# ---------------------------------------------------------------------------

@lru_cache
def get_gemini_service() -> GeminiService:
    return GeminiService(client=get_genai_client(), settings=get_settings())


@lru_cache
def get_universal_llm_service() -> UniversalLLMService:
    return UniversalLLMService(genai_client=get_genai_client(), settings=get_settings())


@lru_cache
def get_gemini_api_client():
    """Non-Vertex Gemini API client — image generation must not use Vertex RPM.

    Doppler often sets GOOGLE_GENAI_USE_VERTEXAI / GOOGLE_GENAI_USE_ENTERPRISE for
    Veo + ADC. Those flags make google.genai prefer aiplatform.googleapis.com.
    We pop them only while constructing this client so Imagen calls use the
    developer API (GEMINI_API_KEY, generativelanguage.googleapis.com).
    """
    import logging
    import os

    from google import genai as _genai

    log = logging.getLogger(__name__)
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in Doppler genflow/prd")

    _saved_vert = os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
    _saved_ent = os.environ.pop("GOOGLE_GENAI_USE_ENTERPRISE", None)
    try:
        client = _genai.Client(api_key=api_key.strip(), vertexai=False)
    finally:
        if _saved_vert is not None:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = _saved_vert
        if _saved_ent is not None:
            os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = _saved_ent

    if getattr(client, "vertexai", False):
        raise RuntimeError(
            "Gemini image client initialized with vertexai=True — check google-genai SDK / env."
        )
    try:
        base_url = client._api_client._http_options.base_url or ""
    except Exception:  # pragma: no cover
        base_url = ""
    if not base_url or "generativelanguage" not in base_url:
        raise RuntimeError(
            "Gemini image client must use generativelanguage.googleapis.com "
            f"(got base_url={base_url!r}). "
            "Unset GOOGLE_GENAI_USE_VERTEXAI / GOOGLE_GENAI_USE_ENTERPRISE for this client or fix SDK."
        )
    log.info("Gemini developer API client ready for image generation (base_url=%s)", base_url)
    return client


@lru_cache
def get_gemini_image_service() -> GeminiImageService:
    # Product / storyboard / avatar (non-Imagen) images: use Gemini API + API key
    # so requests hit generativelanguage.googleapis.com, not Vertex Imagen RPM.
    return GeminiImageService(client=get_gemini_api_client(), settings=get_settings())


@lru_cache
def get_imagen_service() -> ImagenService:
    return ImagenService(client=get_genai_client(), settings=get_settings())


@lru_cache
def get_veo_service() -> VeoService:
    return VeoService(client=get_genai_client(), settings=get_settings())


# ---------------------------------------------------------------------------
# Application services
# ---------------------------------------------------------------------------

@lru_cache
def get_input_service() -> InputService:
    return InputService(
        gemini=get_gemini_service(),
        gemini_image=get_gemini_image_service(),
        storage=get_local_storage(),
        settings=get_settings(),
    )


@lru_cache
def get_qc_service() -> QCService:
    return QCService(gemini=get_universal_llm_service(), settings=get_settings())


@lru_cache
def get_script_service() -> ScriptService:
    return ScriptService(
        gemini=get_universal_llm_service(),
        storage=get_local_storage(),
        settings=get_settings(),
    )


@lru_cache
def get_avatar_service() -> AvatarService:
    return AvatarService(
        gemini_image=get_gemini_image_service(),
        imagen=get_imagen_service(),
        storage=get_local_storage(),
        settings=get_settings(),
    )


@lru_cache
def get_storyboard_service() -> StoryboardService:
    return StoryboardService(
        gemini_image=get_gemini_image_service(),
        qc=get_qc_service(),
        storage=get_local_storage(),
        settings=get_settings(),
    )


@lru_cache
def get_video_service() -> VideoService:
    return VideoService(
        veo=get_veo_service(),
        gcs=get_gcs_storage(),
        qc=get_qc_service(),
        storage=get_local_storage(),
        settings=get_settings(),
    )


@lru_cache
def get_stitch_service() -> StitchService:
    return StitchService(storage=get_local_storage())


def get_review_service() -> ReviewService:
    global _review_service
    if _review_service is None:
        _review_service = ReviewService(db=get_database())
    return _review_service


def get_log_service() -> LogService:
    global _log_service
    if _log_service is None:
        _log_service = LogService(db=get_database())
    return _log_service


def get_pipeline_service() -> PipelineService:
    return PipelineService(
        script_svc=get_script_service(),
        avatar_svc=get_avatar_service(),
        storyboard_svc=get_storyboard_service(),
        video_svc=get_video_service(),
        stitch_svc=get_stitch_service(),
        review_svc=get_review_service(),
        job_store=get_job_store(),
        event_broadcaster=get_broadcaster(),
    )


def get_bulk_service() -> BulkService:
    return BulkService(
        pipeline_svc=get_pipeline_service(),
        job_store=get_job_store(),
    )
