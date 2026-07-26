# Jiwer-api — Tổng quan kế hoạch

## Mục tiêu

Triển khai REST API đo **Word Error Rate (WER)** dựa trên thư viện [jiwer](https://pypi.org/project/jiwer/) (v4.x), gồm:

1. **API đơn** — đo WER của 1 cặp câu (reference ↔ hypothesis)
2. **API batch** — đo WER của nhiều câu; dùng **Gemini** tìm anchors rồi **span merge** vùng lệch (gộp biên + text lệch → 1 cặp) để đảm bảo số phần tử bằng nhau trước khi gọi jiwer
3. **Docker** — đóng gói chạy được bằng Docker / Docker Compose

## Phân tích jiwer (tóm tắt)

| Hạng mục | Chi tiết |
|---|---|
| Package | `jiwer` ≥ 4.0.0 (Python ≥ 3.8) |
| Core deps | `rapidfuzz`, `click` |
| Metrics | WER, MER, WIL, WIP, CER |
| Single | `jiwer.wer(ref, hyp)` hoặc `jiwer.process_words(ref, hyp)` |
| Batch | `jiwer.wer([ref...], [hyp...])` — **bắt buộc** `len(refs) == len(hyps)` |
| Chi tiết | `process_words` → `WordOutput` (wer, hits, substitutions, insertions, deletions, alignments) |
| Transform | Default normalize (lowercase, strip punctuation, …) qua `wer_default` |

**Công thức WER:**

```
WER = (S + D + I) / N
```

- `S` substitutions, `D` deletions, `I` insertions, `N` số từ trong reference

**Ràng buộc quan trọng cho batch:** jiwer yêu cầu 1-1 mapping giữa reference và hypothesis theo thứ tự index. API batch: Gemini chọn anchors → **span merge** (xem `03-gemini-alignment.md`) → jiwer.

## Các phase (plan)

| Phase | File | Nội dung | Phụ thuộc duyệt |
|---|---|---|---|
| 0 | `00-overview.md` | Tổng quan (file này) | — |
| 1 | `01-architecture.md` | Kiến trúc hệ thống, stack, cấu trúc thư mục | ✅ |
| 2 | `02-api-design.md` | Thiết kế endpoint, request/response schema | ✅ |
| 3 | `03-gemini-alignment.md` | Chiến lược Gemini so khớp batch | ✅ |
| 4 | `04-implementation.md` | Kế hoạch implement chi tiết từng module | ✅ |
| 5 | `05-docker.md` | Dockerfile, Compose, env, deploy | ✅ |
| 6 | `06-testing.md` | Test plan, ví dụ curl | ✅ |

## Triển khai code (bắt đầu từ Phase 0 skeleton)

| Code phase | Phạm vi | Status |
|---|---|---|
| **0 — Skeleton** | Cấu trúc app, config, `GET /health`, stub router (xem `PHASE-0.md`) | ✅ |
| 1+ | WER single, Gemini align, batch, Docker, tests đầy đủ | ⏳ |

## Nguyên tắc triển khai

1. Plan đã lưu trong `plans/`; code triển khai theo từng phase (bắt đầu Phase 0 skeleton).
2. Mỗi phase plan có mục **Quyết định cần duyệt** — mặc định dùng đề xuất trong `CHECKLIST.md` nếu không có feedback ngược.
3. Commit/push liên tục theo từng code phase.

## Repo

- GitHub: https://github.com/hieuvt/Jiwer-api
- Branch làm việc hiện tại: `cursor/wer-api-plan-8443`

## Cách duyệt

Vui lòng review từng file trong `plans/`, đặc biệt các mục **Quyết định cần duyệt**.  
Phản hồi dạng:

- `Approve all` — bắt đầu implement theo plan
- `Approve with changes: …` — chỉnh plan rồi implement
- `Revise phase X: …` — sửa phase cụ thể trước
