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
- `app/main.py` mount router + CORS (optional) + exception handlers
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
- Schema Pydantic + validation (non-empty strings — **cho phép empty?** theo jiwer 4.x empty được định nghĩa; đề xuất **cho phép** empty string)
- Unit tests với cases cố định

### Step 4.4 — Gemini aligner

- `GeminiAligner.align(references, hypotheses) -> AlignmentResult`
- Prompt + structured JSON
- Validate indices / uniqueness
- Apply `drop_unmatched` + `min_confidence`
- Unit tests với **mock** response (không cần API key trong CI)

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
5. **Idempotent:** cùng input → cùng WER (alignment Gemini có thể non-deterministic nhẹ → cân nhắc `temperature=0`).

## Quyết định cần duyệt

1. Cho phép `reference=""` / `hypothesis=""` (theo jiwer 4.x) hay reject?
2. `temperature=0` cho Gemini alignment — OK?
3. CORS: mở `*` cho dev hay không CORS?

## Acceptance criteria (Phase 4)

- [ ] Hai endpoint hoạt động local với `.env`
- [ ] Tests xanh (mock Gemini)
- [ ] README đủ chạy được
