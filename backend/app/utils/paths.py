"""Resolve public /output/... URLs to local filesystem paths."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_output_local_path(image_url: str, output_base: Path) -> Path | None:
    """Map a browser or API image URL to a file under ``output_base``.

    Handles:
    - ``/output/...`` (local dev, internal API contract)
    - ``{BASE_PATH}/output/...`` (e.g. ``/genflow/output/...`` behind nginx)
    """
    u = (image_url or "").strip()
    if not u:
        return None
    base = os.environ.get("BASE_PATH", "").strip().rstrip("/")
    prefixes: list[str] = []
    if base:
        prefixes.append(f"{base}/output/")
    prefixes.append("/output/")
    root = output_base.resolve()
    for pref in prefixes:
        if u.startswith(pref):
            rel = u[len(pref) :].lstrip("/")
            if not rel:
                return None
            return root / rel
    return None
