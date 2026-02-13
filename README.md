# Frontend Dashboard

Quick instructions to run the local demo dashboard.

1. Start the demo API (FastAPI + Uvicorn)

```bash
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Start on port 8000 (recommended)
uvicorn web.server:app --host 0.0.0.0 --port 8000 --reload
```

2. Serve the frontend files (so fetch() works from browser)

```bash
# From project root (serves on port 8080)
python3 -m http.server 8080 --directory frontend
# Open http://localhost:8080 in your browser
```

Notes:
- The frontend will automatically try to use the same origin `/api` when served via HTTP, and falls back to `http://127.0.0.1:8000/api` when opened via `file://` or when a direct origin is not available. If you run the demo API on a different host/port, set `window.FIRE_MAMBA_API` to your API root before loading `app.js` (advanced).
- Example: to test against port 8000 (default used in this README) the validator and tests use the env var `API_URL`.

Examples:

```bash
# Run validator against port 8000
cd web
source venv/bin/activate
API_URL=http://127.0.0.1:8000 python validate_api.py

# Run smoke tests
API_URL=http://127.0.0.1:8000 python test_api.py
```
