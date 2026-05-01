#!/usr/bin/env python3
"""One-shot: read local .env, service-account.json, ~/.modal.toml and push
into Doppler genflow/<config> via the REST API.

Usage:  python3 _doppler_push.py <config>          # e.g. dev or prd
        DOPPLER_TOKEN=<dp...> python3 _doppler_push.py dev
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()


def load_doppler_token() -> str:
    if t := os.environ.get("DOPPLER_TOKEN"):
        return t
    cfg = HOME / ".doppler" / ".doppler.yaml"
    if cfg.exists():
        for line in cfg.read_text().splitlines():
            m = re.search(r"\btoken:\s*(\S+)", line)
            if m:
                return m.group(1)
    sys.exit("ERROR: no DOPPLER_TOKEN env var and no token in ~/.doppler/.doppler.yaml")


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        out[k.strip()] = v
    return out


def parse_modal_toml(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    text = path.read_text()
    for key in ("token_id", "token_secret"):
        m = re.search(rf'^\s*{key}\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            out[f"MODAL_{key.upper()}"] = m.group(1)
    return out


def build_secrets() -> dict[str, str]:
    secrets: dict[str, str] = {}
    secrets.update(parse_env(REPO / ".env"))

    # Sensible defaults from .env.example, only added if not already set.
    defaults = {
        "GEMINI_FLASH_MODEL": "gemini-3-flash-preview",
        "OUTPUT_DIR": "output",
        "STORYBOARD_QC_THRESHOLD": "60",
        "VIDEO_QC_THRESHOLD": "6",
    }
    for k, v in defaults.items():
        secrets.setdefault(k, v)

    sa = REPO / "service-account.json"
    if sa.exists():
        sa_text = sa.read_text().strip()
        json.loads(sa_text)
        secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = sa_text

    secrets.update(parse_modal_toml(HOME / ".modal.toml"))
    return secrets


def push(token: str, project: str, config: str, secrets: dict[str, str]) -> None:
    payload = {
        "project": project,
        "config": config,
        "secrets": dict(secrets),
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.doppler.com/v3/configs/config/secrets",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if not result.get("success", True) and "secrets" not in result:
        print("ERROR:", json.dumps(result, indent=2))
        sys.exit(1)
    keys = sorted(result.get("secrets", {}).keys()) or sorted(secrets.keys())
    print(f"Pushed {len(secrets)} secrets into {project}/{config}:")
    for k in keys:
        if k in secrets:
            v = secrets[k]
            preview = (v[:24] + "…") if len(v) > 24 else v
            preview = preview.replace("\n", " ")
            print(f"  {k:42s} = {preview}")


def main() -> None:
    config = sys.argv[1] if len(sys.argv) > 1 else "dev"
    token = load_doppler_token()
    secrets = build_secrets()
    if not secrets:
        sys.exit("Nothing to push (no .env / service-account.json / .modal.toml found).")
    push(token, "genflow", config, secrets)


if __name__ == "__main__":
    main()
