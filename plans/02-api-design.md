# Phase 2 — API Design

## Endpoints

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/health` | Health check (Docker / K8s) |
| `POST` | `/api/v1/wer` | WER 1 cặp câu |
| `POST` | `/api/v1/wer/batch` | WER batch + Gemini alignment |

---

## 1) `POST /api/v1/wer` — Single

### Request

```json
{
  "reference": "xin chào thế giới",
  "hypothesis": "xin chào thế giới ạ",
  "include_details": true
}
```

| Field | Type | Required | Default | Mô tả |
|---|---|---|---|---|
| `reference` | string | ✅ | — | Câu chuẩn (ground truth) |
| `hypothesis` | string | ✅ | — | Câu ASR / dự đoán |
| `include_details` | bool | ❌ | `true` | Trả thêm hits/S/D/I/alignment |

### Response `200`

```json
{
  "wer": 0.25,
  "mer": 0.2,
  "wil": 0.3,
  "wip": 0.7,
  "hits": 3,
  "substitutions": 0,
  "insertions": 1,
  "deletions": 0,
  "reference": "xin chào thế giới",
  "hypothesis": "xin chào thế giới ạ",
  "alignment_viz": "optional string from jiwer.visualize_alignment"
}
```

Khi `include_details=false`, chỉ trả `wer` (và có thể `mer/wil/wip`).

### Errors

| Code | Khi nào |
|---|---|
| `422` | Thiếu field / type sai |
| `500` | Lỗi nội bộ jiwer |

---

## 2) `POST /api/v1/wer/batch` — Batch + Gemini match

### Request

```json
{
  "references": [
    "xin chào thế giới",
    "hôm nay trời đẹp",
    "tôi thích cà phê"
  ],
  "hypotheses": [
    "hôm nay trời đẹp quá",
    "xin chào thế giới",
    "tôi thích trà"
  ],
  "include_details": true,
  "include_alignment_meta": true,
  "drop_unmatched": false
}
```

| Field | Type | Required | Default | Mô tả |
|---|---|---|---|---|
| `references` | `string[]` | ✅ | — | Danh sách câu chuẩn (≥1) |
| `hypotheses` | `string[]` | ✅ | — | Danh sách câu hypothesis (≥1) |
| `include_details` | bool | ❌ | `true` | Chi tiết metrics + per-pair |
| `include_alignment_meta` | bool | ❌ | `true` | Trả mapping Gemini đã dùng |
| `drop_unmatched` | bool | ❌ | `false` | Nếu `true`: bỏ cặp không match; nếu `false` + lệch số lượng → error hoặc pad (xem Phase 3) |

**Lưu ý:** Input **không cần** cùng độ dài / cùng thứ tự. Gemini sẽ so khớp trước.

### Response `200`

```json
{
  "wer": 0.3333,
  "mer": 0.28,
  "wil": 0.4,
  "wip": 0.6,
  "hits": 8,
  "substitutions": 1,
  "insertions": 2,
  "deletions": 1,
  "num_pairs": 3,
  "pairs": [
    {
      "index": 0,
      "reference": "xin chào thế giới",
      "hypothesis": "xin chào thế giới",
      "ref_index": 0,
      "hyp_index": 1,
      "wer": 0.0
    },
    {
      "index": 1,
      "reference": "hôm nay trời đẹp",
      "hypothesis": "hôm nay trời đẹp quá",
      "ref_index": 1,
      "hyp_index": 0,
      "wer": 0.25
    }
  ],
  "alignment_meta": {
    "model": "gemini-2.0-flash",
    "mappings": [
      {"ref_index": 0, "hyp_index": 1, "confidence": 0.98},
      {"ref_index": 1, "hyp_index": 0, "confidence": 0.95},
      {"ref_index": 2, "hyp_index": 2, "confidence": 0.9}
    ],
    "unmatched_references": [],
    "unmatched_hypotheses": []
  }
}
```

- `wer` ở root = WER **tổng** trên toàn bộ cặp đã align (cách jiwer tính trên list).
- `pairs[].wer` = WER từng cặp (optional, tính bằng cách gọi single trên từng cặp).

### Errors

| Code | Khi nào |
|---|---|
| `422` | List rỗng / schema sai |
| `400` | Không align được đủ cặp (khi `drop_unmatched=false`) |
| `502` | Gemini API lỗi / timeout / parse fail |
| `503` | Thiếu `GEMINI_API_KEY` |
| `500` | Lỗi nội bộ |

---

## Health

```json
GET /health → { "status": "ok", "version": "0.1.0" }
```

---

## Quyết định cần duyệt

1. Có trả thêm **CER** trên cùng endpoint không, hay chỉ WER (+ MER/WIL/WIP)?
2. `pairs[].wer` có cần không (tốn thêm compute nhẹ)?
3. Giới hạn kích thước batch: đề xuất **max 100 câu / request** — OK?
4. Có cần endpoint skip-Gemini (`/wer/batch/raw`) khi client đã tự align sẵn không?
5. Response field naming: tiếng Anh như trên — OK?

## Acceptance criteria (Phase 2)

- [ ] Schema request/response được chốt
- [ ] Error codes được chốt
- [ ] Giới hạn batch & optional endpoints được chốt
