# Phase 0 — Skeleton (đã triển khai)

> Bootstrap dự án theo Step 4.1 trong `04-implementation.md` và cấu trúc thư mục trong `01-architecture.md`.

## Mục tiêu Phase 0

Tạo khung chạy được trước khi implement WER / Gemini / Docker:

1. Cấu trúc thư mục `app/` (api, services, core)
2. `requirements.txt` + `.env.example`
3. `app/config.py` (pydantic-settings)
4. `app/main.py` + `GET /health`
5. Router stub `/api/v1` (chưa có POST WER)
6. Smoke tests (`tests/test_health.py`)
7. README hướng dẫn chạy local

## Acceptance criteria

- [x] `uvicorn app.main:app` khởi động được
- [x] `GET /health` → `{"status":"ok","version":"..."}`
- [x] `pytest` xanh cho health / OpenAPI
- [x] Cấu trúc thư mục khớp architecture đề xuất
- [x] Chưa implement logic WER / Gemini / Docker (để phase sau)

## Quyết định đã áp dụng (mặc định từ CHECKLIST)

- Framework: **FastAPI**
- Prefix: **`/api/v1`**
- Auth: **không**
- Gemini model default: **`gemini-2.0-flash`**
- Port default: **10000**

## Không nằm trong Phase 0

- `POST /api/v1/wer` / `POST /api/v1/wer/batch`
- `wer_service` / `gemini_aligner` logic
- Dockerfile / Compose
- GitHub Actions CI
