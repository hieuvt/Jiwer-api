# Phase 6 — Testing & Verification

## Test strategy

| Loại | Tool | Scope |
|---|---|---|
| Unit | `pytest` | `wer_service`, schema validation |
| Unit (mock) | `pytest` + mock | `gemini_aligner` parse/validate |
| API | `httpx.AsyncClient` / `TestClient` | routes single + batch |
| Manual | `curl` | smoke sau Docker |

## Case matrix — Single WER

| # | reference | hypothesis | Kỳ vọng |
|---|---|---|---|
| 1 | `hello world` | `hello world` | wer = 0 |
| 2 | `hello world` | `hello duck` | wer = 0.5 |
| 3 | `""` | `""` | wer = 0 (nếu cho phép empty) |
| 4 | `""` | `silence` | wer = 1 |
| 5 | tiếng Việt có dấu | biến thể gần | wer hợp lý, không crash |

## Case matrix — Batch + align

| # | Scenario | Kỳ vọng |
|---|---|---|
| 1 | Cùng thứ tự, N=M | mapping identity; WER đúng |
| 2 | Đảo thứ tự 2 câu | Gemini (mock) swap indices; WER đúng theo semantic pair |
| 3 | Thừa 1 hypothesis, `drop_unmatched=true` | 1 unmatched hyp trong meta; vẫn tính |
| 4 | Thừa hyp, `drop_unmatched=false` | 400 (nếu chọn reject) |
| 5 | Gemini timeout | 502 sau retry |
| 6 | Missing API key | 503 |
| 7 | Batch > max (100) | 422 |

## Dependencies test

```
pytest>=8.0
pytest-asyncio>=0.24
```

## Manual curl (sau khi chạy)

```bash
# health
curl -s http://localhost:8000/health

# single
curl -s -X POST http://localhost:8000/api/v1/wer \
  -H 'Content-Type: application/json' \
  -d '{"reference":"hello world","hypothesis":"hello duck"}'

# batch
curl -s -X POST http://localhost:8000/api/v1/wer/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "references":["hello world","i like python"],
    "hypotheses":["i like python","hello duck"]
  }'
```

## CI (optional, ngoài scope tối thiểu)

- GitHub Actions: `pytest` trên PR
- Không gọi Gemini thật trong CI (mock only)

## Quyết định cần duyệt

1. Có setup GitHub Actions trong PR đầu không? (đề xuất: **có, minimal pytest**)
2. Có cần golden-file test cho tiếng Việt cụ thể không?

## Acceptance criteria (Phase 6)

- [ ] `pytest` pass
- [ ] Docker smoke curl pass với Gemini key thật (manual / staging)
