#!/usr/bin/env bash
# Genflow Ad Studio — one-time Doppler bootstrap.
#
# Prereqs (run on your workstation, NOT inside this repo automatically):
#   1. doppler login                                  # personal auth, opens browser
#   2. doppler projects create genflow                # if it doesn't exist
#   3. doppler configs create dev --project genflow
#   4. doppler configs create prd --project genflow   # (when ready)
#
# Then run THIS script once to push the local .env values into Doppler `dev`.
# After verifying `doppler run -- make dev-backend` boots cleanly, you can:
#   - rm /root/genflow-ad-studio/service-account.json
#   - rm /root/.modal.toml
#   - ROTATE both keys in their respective consoles (GCP IAM, modal.com)
#
# Idempotent: re-running just overwrites secrets.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${DOPPLER_PROJECT:-genflow}"
CONFIG="${DOPPLER_CONFIG:-dev}"

echo "Importing into doppler ${PROJECT}/${CONFIG} from ${REPO_DIR}"

if [[ ! -f "${REPO_DIR}/.env" ]]; then
  echo "ERROR: ${REPO_DIR}/.env not found" >&2
  exit 1
fi

# 1) Push every KEY=VALUE from .env into Doppler.
doppler secrets upload "${REPO_DIR}/.env" \
  --project "${PROJECT}" --config "${CONFIG}"

# 2) Inline the GCP service-account JSON as a single secret if present.
SA_FILE="${REPO_DIR}/service-account.json"
if [[ -f "${SA_FILE}" ]]; then
  doppler secrets set GOOGLE_APPLICATION_CREDENTIALS_JSON \
    --project "${PROJECT}" --config "${CONFIG}" \
    "$(cat "${SA_FILE}")"
fi

# 3) Modal token, if it lives in ~/.modal.toml.
MODAL_FILE="${HOME}/.modal.toml"
if [[ -f "${MODAL_FILE}" ]]; then
  TOKEN_ID="$(grep -E '^token_id'     "${MODAL_FILE}" | head -1 | cut -d'"' -f2)"
  TOKEN_SECRET="$(grep -E '^token_secret' "${MODAL_FILE}" | head -1 | cut -d'"' -f2)"
  if [[ -n "${TOKEN_ID}" && -n "${TOKEN_SECRET}" ]]; then
    doppler secrets set MODAL_TOKEN_ID     --project "${PROJECT}" --config "${CONFIG}" "${TOKEN_ID}"
    doppler secrets set MODAL_TOKEN_SECRET --project "${PROJECT}" --config "${CONFIG}" "${TOKEN_SECRET}"
  fi
fi

echo
echo "Done. Verify with:"
echo "  doppler secrets --project ${PROJECT} --config ${CONFIG}"
echo
echo "Then in this repo:"
echo "  doppler setup --project ${PROJECT} --config ${CONFIG}"
echo "  doppler run -- make dev"
