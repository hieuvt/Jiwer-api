# Phase 5 — Docker Packaging

## Mục tiêu

Chạy được bằng:

```bash
docker compose up --build
```

và gọi API tại `http://localhost:10000`.

## Dockerfile (đề xuất multi-stage)

```dockerfile
# build stage: optional nếu chỉ pip install
FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 10000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
```

## docker-compose.yml

```yaml
services:
  wer-api:
    build: .
    ports:
      - "${PORT:-10000}:10000"
    env_file:
      - .env
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.0-flash}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:10000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## .env.example

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_RETRIES=2
GEMINI_MIN_CONFIDENCE=0.0
ALIGNMENT_STRATEGY=span_merge
PORT=10000
LOG_LEVEL=INFO
```

## .dockerignore

```
.git
.env
plans/
tests/
__pycache__/
*.pyc
.venv/
.pytest_cache/
README.md
```

## Bảo mật container

- Không bake `GEMINI_API_KEY` vào image — chỉ inject runtime qua env / compose
- Chạy non-root user (optional hardening — đề xuất có)
- Không expose port nội bộ khác ngoài 10000

## Quyết định cần duyệt / đã chốt

1. Port host mặc định **`10000`** — ✅ đã chốt
2. Có cần image publish lên GHCR/Docker Hub trong scope này không? (đề xuất: **chưa**, chỉ Dockerfile local)
3. Có thêm `docker compose` profile `dev` với `--reload` không?

## Acceptance criteria (Phase 5)

- [ ] `docker compose up --build` thành công
- [ ] `/health` OK trong container
- [ ] Single + batch gọi được từ host
