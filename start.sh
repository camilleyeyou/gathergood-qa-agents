#!/bin/bash
set -e

export PLAYWRIGHT_BROWSERS_PATH=/app/.browsers

echo "=== Installing Playwright Chromium ==="
python -m playwright install --with-deps chromium 2>&1
echo "=== Playwright install complete ==="

# Verify the browser binary exists
if [ -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
    echo "=== Browser cache contents ==="
    find $PLAYWRIGHT_BROWSERS_PATH -name "chrome*" -type f 2>/dev/null | head -5
else
    echo "WARNING: Browser path $PLAYWRIGHT_BROWSERS_PATH does not exist after install"
fi

echo "=== Starting uvicorn ==="
exec uvicorn api.persona_runner:app --host 0.0.0.0 --port ${PORT:-8000}
