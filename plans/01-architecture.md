# Phase 1 — Architecture & Tech Stack

## Stack đề xuất

| Layer | Choice | Lý do |
|---|---|---|
| Language | Python 3.11+ | jiwer yêu cầu ≥3.8; 3.11 ổn định, phổ biến trong Docker |
| Web framework | **FastAPI** | Typed schemas (Pydantic), OpenAPI tự động, async sẵn |
| WER engine | `jiwer` ≥ 4.0 | Thư viện chuẩn, hỗ trợ single + list batch |
| LLM alignment | **Google Gemini** (`google-genai` SDK) | Yêu cầu task: so khớp batch reference/hypothesis |
| Config | `pydantic-settings` + `.env` | Quản lý `GEMINI_API_KEY`, model name, port |
| Server | `uvicorn` | ASGI chuẩn cho FastAPI |
| Container | Docker multi-stage + Compose | Yêu cầu đóng gói |

## Cấu trúc thư mục đề xuất

```
Jiwer-api/
├── plans/                          # Kế hoạch (đã có)
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry
│   ├── config.py                   # Settings từ env
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_wer.py           # POST /wer , POST /wer/batch
│   │   └── schemas.py              # Request/Response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── wer_service.py          # Wrapper jiwer (single + aligned batch)
│   │   └── gemini_aligner.py       # Gemini: match refs ↔ hyps
│   └── core/
│       ├── __init__.py
│       └── exceptions.py           # Custom HTTP errors
├── tests/
│   ├── test_wer_single.py
│   ├── test_wer_batch.py
│   └── test_gemini_aligner.py      # mock Gemini
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── requirements.txt
├── pyproject.toml                  # optional; hoặc chỉ requirements.txt
└── README.md
```

## Luồng xử lý

### API 1 — Single pair

```
Client → POST /api/v1/wer
       → validate schema
       → wer_service.compute_single(ref, hyp)
       → jiwer.process_words(...)
       → JSON response (wer + chi tiết)
```

### API 2 — Batch + Gemini anchors + span merge

```
Client → POST /api/v1/wer/batch
       → validate schema (lists có thể lệch số lượng / thứ tự)
       → gemini_aligner.align(references, hypotheses, strategy=span_merge)
            • Gemini trả anchors (mốc khớp semantic, monotonic)
            • Span merge: gộp vùng lệch (biên + text giữa) → cặp đồng length
            • Đảm bảo len(aligned_refs) == len(aligned_hyps)
       → wer_service.compute_batch(aligned_refs, aligned_hyps)
       → jiwer.process_words(list, list)
       → JSON (overall WER + per-pair + alignment meta)
```

## Biên giới trách nhiệm

| Module | Làm gì | Không làm gì |
|---|---|---|
| `routes_wer.py` | HTTP, validation, status code | Logic WER / Gemini |
| `wer_service.py` | Gọi jiwer, format metrics | Gọi Gemini / merge |
| `gemini_aligner.py` | Prompt anchors + **span merge** deterministic | Tính WER |
| `config.py` | Env, defaults | Business logic |

## Quyết định đã chốt (2026-07-26)

| # | Hạng mục | Quyết định |
|---|---|---|
| 1 | Framework | **FastAPI** |
| 2 | Prefix API | **`/api/v1/...`** |
| 3 | Auth | **Không** (internal service) |
| 4 | Gemini model mặc định | **`gemini-2.0-flash`** |
| 5 | Ngôn ngữ hỗ trợ | **Tiếng Việt + English** (ưu tiên) |

## Acceptance criteria (Phase 1)

- [x] Stack & cấu trúc thư mục được chốt
- [x] Các quyết định trên có câu trả lời rõ
