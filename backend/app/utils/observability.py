"""Langfuse + OpenInference initialization for Genflow Ad Studio.

Idempotent and silent: a no-op when LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
are not set, so local dev works unchanged. When keys ARE present (typically
injected by Doppler), every ADK agent step, every google-genai call (Gemini,
Imagen, Veo), and every @observe-decorated function is captured as a trace
in Langfuse.

Must run BEFORE google-adk and google-genai are imported by application code,
so we wire it up in bootstrap.py which is the very first app import.
"""
from __future__ import annotations

import logging
import os
from typing import Final

_LOG = logging.getLogger(__name__)
_MARKER: Final = "_GENFLOW_LANGFUSE_INITIALIZED"


def _enabled() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY")) and bool(
        os.environ.get("LANGFUSE_SECRET_KEY")
    )


def init_observability() -> None:
    if os.environ.get(_MARKER):
        return
    os.environ[_MARKER] = "noop"

    if not _enabled():
        _LOG.info("Langfuse keys not set; observability disabled.")
        return

    try:
        from langfuse import get_client
    except ImportError:
        _LOG.warning("langfuse SDK not installed; skipping observability init.")
        return

    client = get_client()
    try:
        ok = client.auth_check()
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("Langfuse auth_check failed: %s", exc)
        ok = False

    if not ok:
        _LOG.warning("Langfuse credentials present but auth failed; spans will not export.")
        return

    _instrument_google_adk()
    _instrument_google_genai()

    os.environ[_MARKER] = "active"
    _LOG.info(
        "Langfuse observability active (host=%s, release=%s).",
        os.environ.get("LANGFUSE_BASE_URL", os.environ.get("LANGFUSE_HOST", "<default>")),
        os.environ.get("LANGFUSE_RELEASE", "<unset>"),
    )


def _instrument_google_adk() -> None:
    try:
        from openinference.instrumentation.google_adk import GoogleADKInstrumentor

        GoogleADKInstrumentor().instrument()
        _LOG.debug("GoogleADKInstrumentor active.")
    except ImportError:
        _LOG.info("openinference-instrumentation-google-adk not installed; ADK spans skipped.")
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("Failed to instrument google-adk: %s", exc)


def _instrument_google_genai() -> None:
    try:
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

        GoogleGenAIInstrumentor().instrument()
        _LOG.debug("GoogleGenAIInstrumentor active.")
    except ImportError:
        _LOG.info(
            "openinference-instrumentation-google-genai not installed; "
            "Gemini/Imagen/Veo spans skipped."
        )
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("Failed to instrument google-genai: %s", exc)


init_observability()
