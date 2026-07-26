# Jiwer-api

REST API đo **Word Error Rate (WER)** dựa trên [jiwer](https://pypi.org/project/jiwer/) (v4.x), kèm Gemini để so khớp batch reference/hypothesis.

## Trạng thái

**Phase 0 — Skeleton** đã triển khai:

- Cấu trúc thư mục FastAPI theo `plans/01-architecture.md`
- `GET /health`
- Config từ env (`.env.example`)
- Router `/api/v1` (endpoint WER sẽ bổ sung ở phase sau)
- Plans trong `plans/`

| Phase | Nội dung | Status |
|---|---|---|
| 0 | Skeleton + health | ✅ |
| 1+ | WER single / batch + Gemini + Docker | ⏳ |

Chi tiết kế hoạch: xem [`plans/`](./plans/).

## Yêu cầu

- Python 3.11+
- (Sau này) `GEMINI_API_KEY` cho API batch

## Cài đặt local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Chạy

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

- Health: http://localhost:10000/health
- OpenAPI docs: http://localhost:10000/docs

```bash
curl -s http://localhost:10000/health
# {"status":"ok","version":"0.1.0"}
```

## Test

```bash
pytest -q
```

## API (roadmap)

| Method | Path | Phase |
|---|---|---|
| `GET` | `/health` | 0 |
| `POST` | `/api/v1/wer` | sau |
| `POST` | `/api/v1/wer/batch` | sau (Gemini align) |

## Docker

Sẽ bổ sung ở phase Docker (`plans/05-docker.md`).
