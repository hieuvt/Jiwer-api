# Jiwer-api — Tổng quan kế hoạch

## Mục tiêu

Triển khai REST API đo **Word Error Rate (WER)** dựa trên thư viện [jiwer](https://pypi.org/project/jiwer/) (v4.x), gồm:

1. **API đơn** — đo WER của 1 cặp câu (reference ↔ hypothesis)
2. **API batch** — đo WER của nhiều câu; dùng **Gemini** tự động so khớp (align) reference & hypothesis để đảm bảo số phần tử bằng nhau trước khi gọi jiwer
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

**Ràng buộc quan trọng cho batch:** jiwer yêu cầu 1-1 mapping giữa reference và hypothesis theo thứ tự index. Vì vậy API batch phải dùng Gemini để match/align trước khi tính.

## Các phase

| Phase | File | Nội dung | Phụ thuộc duyệt |
|---|---|---|---|
| 0 | `00-overview.md` | Tổng quan (file này) | — |
| 1 | `01-architecture.md` | Kiến trúc hệ thống, stack, cấu trúc thư mục | ✅ |
| 2 | `02-api-design.md` | Thiết kế endpoint, request/response schema | ✅ |
| 3 | `03-gemini-alignment.md` | Chiến lược Gemini so khớp batch | ✅ |
| 4 | `04-implementation.md` | Kế hoạch implement chi tiết từng module | ✅ |
| 5 | `05-docker.md` | Dockerfile, Compose, env, deploy | ✅ |
| 6 | `06-testing.md` | Test plan, ví dụ curl | ✅ |

## Nguyên tắc triển khai (sau khi duyệt)

1. **Không code** cho đến khi plan được duyệt (hoặc chỉnh sửa theo feedback).
2. Mỗi phase có mục **Quyết định cần duyệt** — các lựa chọn kỹ thuật chờ confirm.
3. Sau duyệt: implement theo thứ tự Phase 1 → 6, commit/push liên tục.

## Repo

- GitHub: https://github.com/hieuvt/Jiwer-api
- Branch làm việc hiện tại: `cursor/wer-api-plan-8443`

## Cách duyệt

Vui lòng review từng file trong `plans/`, đặc biệt các mục **Quyết định cần duyệt**.  
Phản hồi dạng:

- `Approve all` — bắt đầu implement theo plan
- `Approve with changes: …` — chỉnh plan rồi implement
- `Revise phase X: …` — sửa phase cụ thể trước
