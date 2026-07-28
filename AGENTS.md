# AGENTS.md

## Cursor Cloud specific instructions

`jiwer-api` is a single Python 3 FastAPI service that computes Word Error Rate (WER). There is no database and no frontend. Standard commands live in `README.md`.

- Dependencies install into a virtualenv at `.venv` (the update script creates it and installs `requirements-dev.txt`). Activate with `source .venv/bin/activate` or call binaries directly, e.g. `.venv/bin/pytest`, `.venv/bin/uvicorn`.
- Run tests: `GEMINI_API_KEY="" .venv/bin/pytest -q`. Tests mock Gemini, so no real key is needed (this mirrors CI in `.github/workflows/tests.yml`).
- Run the dev server: `GEMINI_API_KEY="" .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload`. Swagger UI at `/docs`, health at `/health`.
- No linter is configured in this repo.
- `GEMINI_API_KEY` is only required for the `POST /api/v1/wer/batch` endpoint. `/health` and single-pair `POST /api/v1/wer` work without any key. To exercise batch alignment end-to-end, set a real `GEMINI_API_KEY` (add it as a secret).
- The repo targets Python 3.11 (Dockerfile/CI), but it also runs fine on the system Python 3.12 used here.
