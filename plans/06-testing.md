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
| 3 | `""` | `""` | **422** (reject empty — đã chốt Phase 4) |
| 4 | `""` | `silence` | **422** |
| 5 | tiếng Việt có dấu | biến thể gần | wer hợp lý, không crash |

## Case matrix — Batch + align (`span_merge`)

| # | Scenario | Kỳ vọng |
|---|---|---|
| 1 | Cùng thứ tự, N=M, anchors identity | giữ từng cặp; WER đúng; `merged_spans` rỗng |
| 2 | Đảo thứ tự 2 câu | Gemini (mock) anchors swap; WER đúng theo semantic pair |
| 3 | Hyp thừa 1 câu giữa 2 anchors | span merge vùng giữa → 1 cặp gộp; `merged=true`; đủ text trong WER |
| 4 | Ref thừa 1 câu giữa 2 anchors | tương tự — merge phía ref |
| 5 | 0 anchors (Gemini rỗng OK) | merge **toàn batch** thành 1 cặp |
| 6 | Gemini timeout | 502 sau retry |
| 7 | Missing API key | 503 |
| 8 | Batch > max (100) | 422 |
| 9 | Lệch ở đầu/cuối (1 biên) | merge từ đầu→anchor / anchor→cuối |

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
