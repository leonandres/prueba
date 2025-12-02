#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
API_TOKEN=${API_TOKEN:-secret-token}
FILE_SIZE_LIMIT_MB=${FILE_SIZE_LIMIT_MB:-5}
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
