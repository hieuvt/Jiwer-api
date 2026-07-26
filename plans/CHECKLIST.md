# Checklist duyệt nhanh

Đánh dấu / trả lời các mục dưới đây rồi reply `Approve all` hoặc `Approve with changes: ...`.

## Quyết định tổng hợp

### Architecture (`01`) — ✅ Đã chốt

- [x] Framework: **FastAPI**
- [x] Prefix: **`/api/v1`**
- [x] Auth: **Không** (internal)
- [x] Gemini model: **`gemini-2.0-flash`**
- [x] Ngôn ngữ: **VI + EN**

### API Design (`02`) — ✅ Đã chốt (mặc định checklist)

- [x] Metrics: **WER + MER/WIL/WIP** (không CER mặc định)
- [x] Per-pair WER trong batch: **Có**
- [x] Max batch: **100**
- [x] Endpoint raw (skip Gemini): **Chưa làm**
- [x] Field names tiếng Anh

### Gemini Alignment (`03`) — ✅ Đã chốt

- [x] Reconcile lệch câu: **`span_merge`**
- [x] `GEMINI_MIN_CONFIDENCE` default: **0.0**
- [x] Trả `reason` từ Gemini: **Có**
- [x] Batch lớn: **1 lần gọi Gemini** (≤100)
- [x] SDK: **`google-genai`**

### Implementation (`04`) — ✅ Đã chốt

- [x] Empty strings: **Reject** (`422`)
- [x] Gemini `temperature=0`
- [x] CORS: **Không**

### Docker (`05`) — ✅ Đã chốt

- [x] Port **10000**
- [x] Không publish registry
- [x] Non-root user trong image: **Có**
- [x] Compose profile `dev` / `--reload`: **Không** (1 compose đơn giản)

### Testing (`06`) — ✅ Đã chốt

- [x] GitHub Actions pytest: **Có**
- [x] Golden tests tiếng Việt: **Có vài case**

## Phạm vi ngoài (không làm trừ khi yêu cầu)

- Auth OAuth / JWT
- Rate limiting phức tạp
- DB lưu lịch sử WER
- UI frontend
- CER-only endpoint riêng
- Multi-tenant
- Compose profile `dev`
- Publish image registry
