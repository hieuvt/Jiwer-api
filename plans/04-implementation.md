# Phase 4 — Implementation Plan

> Chỉ triển khai **sau khi** Phase 1–3 được duyệt.

## Thứ tự implement

### Step 4.1 — Skeleton project

- Tạo cấu trúc thư mục theo Phase 1
- `requirements.txt`:

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
jiwer>=4.0.0
pydantic>=2.0
pydantic-settings>=2.0
google-genai>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
```

- `app/config.py` đọc env
- `app/main.py` mount router + exception handlers (**không CORS**)
- `GET /health`

### Step 4.2 — WER service (không Gemini)

- `wer_service.compute_single(reference, hypothesis, include_details)`
  - Dùng `jiwer.process_words`
  - Map `WordOutput` → dict response
  - Optional: `jiwer.visualize_alignment(out)` nếu `include_details`
- `wer_service.compute_batch(refs, hyps, include_details)`
  - Assert `len(refs)==len(hyps)` (internal invariant)
  - Overall metrics từ 1 lần `process_words`
  - Per-pair WER: loop `process_words` từng cặp (nếu cần)

### Step 4.3 — Single endpoint

- `POST /api/v1/wer`
- Schema Pydantic + validation: **reject** empty string (`reference` / `hypothesis` phải non-empty sau strip — `422`)
- Unit tests với cases cố định

### Step 4.4 — Gemini aligner + span merge

- `GeminiAligner.align(references, hypotheses, strategy="span_merge") -> AlignmentResult`
- Prompt + structured JSON → **anchors** (không drop/pad)
- Validate indices / uniqueness / monotonic
- Apply `min_confidence`, rồi **span merge** deterministic (xem Phase 3)
- Meta: `anchors`, `merged_spans`, `num_pairs_after_merge`
- Unit tests với **mock** Gemini + case lệch số câu (không cần API key trong CI)

### Step 4.5 — Batch endpoint

- `POST /api/v1/wer/batch`
- Gọi aligner → wer_service
- Error mapping: 400 / 502 / 503
- Integration test với mock Gemini

### Step 4.6 — Docs & examples

- Cập nhật `README.md`: cài đặt, env, curl examples, Docker
- OpenAPI tự động từ FastAPI (`/docs`)

## Chi tiết kỹ thuật đáng chú ý

1. **Normalization:** dùng default transform của jiwer (`wer_default`) — không custom trừ khi yêu cầu thêm.
2. **Float round:** làm tròn metrics 4–6 chữ số thập phân trong response (đề xuất 6).
3. **Logging:** request id / pair counts / Gemini latency — không log full API key.
4. **Timeouts:** Gemini call có timeout từ config.
5. **Idempotent:** cùng input → cùng WER; Gemini alignment dùng **`temperature=0`**.

## Quyết định đã chốt (Phase 4)

1. Empty strings (`reference` / `hypothesis` / phần tử batch): **Reject** → `422` — ✅
2. Gemini `temperature=0` — ✅
3. CORS: **Không** — ✅

## Acceptance criteria (Phase 4)

- [x] Hai endpoint hoạt động local với `.env`
- [x] Tests xanh (mock Gemini)
- [x] README đủ chạy được
