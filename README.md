# Max

A FastAPI-based multi-agent assistant with tools for research, video summarization, website summarization, writing, and music generation.

## Quickstart

Prerequisites

- Python 3.11 (recommended)
- Optional: CUDA drivers if you plan to use GPU packages

### Preferred: uv (fast Python package manager)

1. Install uv (Windows)
   - Run: Invoke-WebRequest -Uri <https://astral.sh/uv/install.ps1> -UseBasicParsing | Invoke-Expression
2. Create and sync env from pyproject
   - uv venv
   - .\.venv\Scripts\Activate.ps1
   - uv sync
3. Run the API
   - uv run python max.py
   - Base URL: <http://localhost:8000>

### Alternative: Conda

- conda env create -f conda-env.yml
- conda activate max
- python max.py

### Alternative: venv + pip

- python -m venv .venv
- .\.venv\Scripts\Activate.ps1
- pip install -r requirements.txt
- python max.py

Smoke test

- GET / returns a greeting
- Review `api/routers/ai_router.py` for request payloads

Notes

- Logs write to `data/logs/` with rotation
- Async-safe tools; heavy IO/CPU offloaded to threads
