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

## 2) `POST /api/v1/wer/batch` — Batch + Gemini anchors + span merge

### Request

```json
{
  "references": [
    "xin chào",
    "hôm nay trời đẹp",
    "tôi thích cà phê"
  ],
  "hypotheses": [
    "xin chào",
    "hôm nay trời",
    "đẹp quá",
    "tôi thích trà"
  ],
  "include_details": true,
  "include_alignment_meta": true,
  "alignment": "span_merge"
}
```

| Field | Type | Required | Default | Mô tả |
|---|---|---|---|---|
| `references` | `string[]` | ✅ | — | Danh sách câu chuẩn (≥1) |
| `hypotheses` | `string[]` | ✅ | — | Danh sách câu hypothesis (≥1) |
| `include_details` | bool | ❌ | `true` | Chi tiết metrics + per-pair |
| `include_alignment_meta` | bool | ❌ | `true` | Trả anchors + merged_spans |
| `alignment` | string | ❌ | `"span_merge"` | Chiến lược reconcile lệch câu (xem Phase 3) |

**Lưu ý:** Input **không cần** cùng độ dài / cùng thứ tự. Gemini tìm **anchors**; vùng lệch được **span merge** (gộp biên + text lệch → 1 cặp). Không dùng `drop_unmatched` / pad rỗng.

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
      "reference": "xin chào",
      "hypothesis": "xin chào",
      "ref_indices": [0],
      "hyp_indices": [0],
      "merged": false,
      "wer": 0.0
    },
    {
      "index": 1,
      "reference": "hôm nay trời đẹp",
      "hypothesis": "hôm nay trời đẹp quá",
      "ref_indices": [1],
      "hyp_indices": [1, 2],
      "merged": true,
      "wer": 0.25
    },
    {
      "index": 2,
      "reference": "tôi thích cà phê",
      "hypothesis": "tôi thích trà",
      "ref_indices": [2],
      "hyp_indices": [3],
      "merged": false,
      "wer": 0.333333
    }
  ],
  "alignment_meta": {
    "model": "gemini-2.0-flash",
    "strategy": "span_merge",
    "anchors": [
      {"ref_index": 0, "hyp_index": 0, "confidence": 0.98, "reason": "same greeting"},
      {"ref_index": 2, "hyp_index": 3, "confidence": 0.9, "reason": "same preference"}
    ],
    "merged_spans": [
      {
        "ref_indices": [1],
        "hyp_indices": [1, 2],
        "merged_reference": "hôm nay trời đẹp",
        "merged_hypothesis": "hôm nay trời đẹp quá"
      }
    ],
    "num_pairs_after_merge": 3
  }
}
```

- `wer` ở root = WER **tổng** trên toàn bộ cặp sau merge (cách jiwer tính trên list).
- `pairs[].wer` = WER từng cặp (sau merge nếu có).
- `pairs[].ref_indices` / `hyp_indices` = index gốc tham gia cặp (1 phần tử nếu không merge).

### Errors

| Code | Khi nào |
|---|---|
| `422` | List rỗng / schema sai / `alignment` không hỗ trợ |
| `400` | Sau merge không còn cặp hợp lệ |
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
