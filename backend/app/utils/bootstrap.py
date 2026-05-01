"""Run-once bootstrap that runs before any google-* SDK imports.

Doppler (and Cloud Run secret mounts, etc.) inject the GCP service-account
as a raw JSON string in `GOOGLE_APPLICATION_CREDENTIALS_JSON`. The Google
SDKs only know how to read a file path from `GOOGLE_APPLICATION_CREDENTIALS`,
so we materialize the JSON to a private tmpfs file and point the standard
env var at it. No-op when the env var isn't present (local dev with a real
file on disk keeps working unchanged).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

_MARKER = "_GENFLOW_ADC_MATERIALIZED"


def materialize_adc() -> None:
    if os.environ.get(_MARKER):
        return
    raw = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not raw:
        os.environ[_MARKER] = "noop"
        return
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and Path(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    ).is_file():
        os.environ[_MARKER] = "preexisting"
        return
    json.loads(raw)
    fd, path = tempfile.mkstemp(prefix="gcp-adc-", suffix=".json")
    try:
        os.write(fd, raw.encode())
    finally:
        os.close(fd)
    os.chmod(path, 0o600)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
    os.environ[_MARKER] = path


materialize_adc()

# Initialize Langfuse + OpenInference instrumentors AFTER ADC is in place but
# BEFORE the application imports google-adk / google-genai (which happens via
# app.api in main.py). Order matters: the instrumentors patch the SDKs at
# import time.
from . import observability  # noqa: E402,F401
