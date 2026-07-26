# Checklist duyệt nhanh

Đánh dấu / trả lời các mục dưới đây rồi reply `Approve all` hoặc `Approve with changes: ...`.

## Quyết định tổng hợp

### Architecture (`01`) — ✅ Đã chốt (2026-07-26)

- [x] Framework: **FastAPI**
- [x] Prefix: **`/api/v1`**
- [x] Auth: **Không** (internal)
- [x] Gemini model: **`gemini-2.0-flash`**
- [x] Ngôn ngữ: **VI + EN**

### API Design (`02`)

- [ ] Metrics: **WER + MER/WIL/WIP** (không CER mặc định) — Đồng ý / Thêm CER
- [ ] Per-pair WER trong batch: **Có** — Đồng ý / Không
- [ ] Max batch: **100** — Đồng ý / Đổi: ______
- [ ] Endpoint raw (skip Gemini): **Chưa làm** — Đồng ý / Thêm
- [ ] Field names tiếng Anh — Đồng ý

### Gemini Alignment (`03`)

- [ ] Unmatched khi `drop_unmatched=false`: **HTTP 400** — Đồng ý / Vẫn tính + warning
- [ ] `GEMINI_MIN_CONFIDENCE` default: **0.0** — Đồng ý / Đổi: ______
- [ ] Trả `reason` từ Gemini: **Có** — Đồng ý / Không
- [ ] Batch lớn: **1 lần gọi Gemini** (≤100) — Đồng ý / Chunk
- [ ] SDK: **`google-genai`** — Đồng ý

### Implementation (`04`)

- [ ] Empty strings: **Cho phép** (theo jiwer 4.x) — Đồng ý / Reject
- [ ] Gemini `temperature=0` — Đồng ý
- [ ] CORS: **Không** (hoặc chỉ dev) — Đồng ý / `*`

### Docker (`05`)

- [ ] Port **8000** — Đồng ý
- [ ] Không publish registry — Đồng ý
- [ ] Non-root user trong image: **Có** — Đồng ý / Bỏ

### Testing (`06`)

- [ ] GitHub Actions pytest: **Có** — Đồng ý / Chưa cần
- [ ] Golden tests tiếng Việt: **Có vài case** — Đồng ý / Không

## Phạm vi ngoài (không làm trừ khi yêu cầu)

- Auth OAuth / JWT
- Rate limiting phức tạp
- DB lưu lịch sử WER
- UI frontend
- CER-only endpoint riêng
- Multi-tenant

## Sau khi duyệt

Agent sẽ:

1. Implement theo Phase 4 → 5 → 6
2. Commit + push branch
3. Mở PR vào `main`
