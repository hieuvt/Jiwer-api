# Jiwer-api

REST API đo **Word Error Rate (WER)** với [jiwer](https://pypi.org/project/jiwer/) v4.x.  
Batch dùng **Gemini anchors + span_merge** để xử lý lệch số câu / thứ tự.

## Tính năng

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/wer` | WER 1 cặp câu |
| `POST` | `/api/v1/wer/batch` | WER batch (Gemini + span_merge) |

- Metrics: WER, MER, WIL, WIP
- Reject empty string (`422`)
- Port mặc định: **10000**
- Không CORS, không auth

## Cài đặt local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# điền GEMINI_API_KEY vào .env
```

Cho dev/test:

```bash
pip install -r requirements-dev.txt

## Chạy

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

- Docs: http://localhost:10000/docs
- Health: http://localhost:10000/health

```bash
curl -s http://localhost:10000/health

curl -s -X POST http://localhost:10000/api/v1/wer \
  -H 'Content-Type: application/json' \
  -d '{"reference":"hello world","hypothesis":"hello duck"}'

curl -s -X POST http://localhost:10000/api/v1/wer/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "references":["xin chào","hôm nay trời đẹp","tôi thích cà phê"],
    "hypotheses":["xin chào","hôm nay trời","đẹp quá","tôi thích trà"]
  }'
```

## Docker

```bash
cp .env.example .env   # set GEMINI_API_KEY
docker compose up --build -d
curl -s http://localhost:10000/health
```

Image chạy **non-root**, port **10000**.

## Test

```bash
pytest -q
```

CI: GitHub Actions workflow `.github/workflows/tests.yml` (mock Gemini, không gọi API thật).

## Env chính

| Biến | Mặc định | Mô tả |
|---|---|---|
| `GEMINI_API_KEY` | — | Bắt buộc cho `/wer/batch` |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Model Gemini |
| `ALIGNMENT_STRATEGY` | `span_merge` | Chiến lược reconcile |
| `PORT` | `10000` | Host port (compose) |
| `MAX_BATCH_SIZE` | `100` | Giới hạn batch |

## Prompt Gemini

System prompt cho batch alignment nằm tại [`docs/prompt.md`](./docs/prompt.md).

## Sample batch

Payload mẫu: [`docs/samples/`](./docs/samples/).
