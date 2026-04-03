#!/bin/sh
# startup.sh — injects UMBRA_API_URL into the frontend HTML at container start
# Used by Render when serving frontend as a static site with env var injection

FRONTEND_FILE="/app/frontend/index.html"

if [ -n "$UMBRA_API_URL" ]; then
  echo "Injecting API URL: $UMBRA_API_URL"
  sed -i "s|window.UMBRA_API_URL.*|window.UMBRA_API_URL = '$UMBRA_API_URL';|g" "$FRONTEND_FILE"
fi

echo "Starting UMBRA backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
