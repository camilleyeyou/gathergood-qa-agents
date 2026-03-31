#!/bin/bash
set -e

echo "=== Installing Playwright Chromium ==="
PLAYWRIGHT_BROWSERS_PATH=/app/.browsers python -m playwright install chromium --with-deps 2>&1 || true
echo "=== Playwright install complete ==="

echo "=== Starting uvicorn ==="
exec uvicorn api.persona_runner:app --host 0.0.0.0 --port ${PORT:-8000}
