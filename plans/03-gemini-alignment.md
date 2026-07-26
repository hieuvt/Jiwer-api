# Phase 3 — Gemini Sentence Alignment + Span Merge

## Vấn đề

jiwer batch yêu cầu:

```python
len(references) == len(hypotheses)
# và references[i] tương ứng hypotheses[i]
```

Trong thực tế, ASR output có thể:

- **Lệch thứ tự** so với transcript gốc
- **Thừa / thiếu** câu (merge/split utterance, hallucination, bỏ sót)
- **Nội dung gần giống** nhưng wording khác → cần semantic match, không chỉ exact string

→ Dùng **Gemini** để tìm các mốc khớp (anchors), rồi **span merge** để gộp vùng lệch thành cặp có cùng độ dài trước khi gọi jiwer.

## Chiến lược đã chốt: `span_merge`

**Không** pad câu rỗng. **Không** drop unmatched làm mặc định. **Không** chia đôi câu thừa.

Khi số câu / ranh giới lệch: gộp **câu biên trái + toàn bộ text lệch giữa + câu biên phải** (mỗi phía) thành **1 câu**, rồi so sánh 1 cặp.

### Vì sao

| Phương án | Đánh giá |
|---|---|
| Pad `""` | Méo WER (deletion/insertion ảo) |
| Drop unmatched | Mất nội dung → WER không cover hết |
| Chia đôi + ghép hàng xóm | Điểm cắt giả, phức tạp |
| **Span merge (chốt)** | Giữ đủ text; jiwer align mức từ trong vùng gộp; đơn giản |

## Luồng align

```
references[N], hypotheses[M]
        │
        ▼
  Build prompt (index-based)
        │
        ▼
  Gemini → anchors[{ref_index, hyp_index, confidence, reason}]
        │
        ▼
  Validate anchors (indices hợp lệ, không trùng, sort theo thứ tự)
        │
        ▼
  Span merge:
        • Duyệt theo thứ tự index tăng dần
        • Vùng giữa 2 anchors liên tiếp (hoặc đầu/cuối) nếu lệch số câu
          → gộp toàn bộ câu trong span (ref) thành 1 chuỗi
          → gộp toàn bộ câu trong span (hyp) thành 1 chuỗi
          → 1 cặp merged
        • Vùng khớp 1-1 sạch → giữ nguyên từng cặp
        │
        ▼
  aligned_refs[], aligned_hyps[]  (cùng length ≥ 1)
        │
        ▼
  jiwer.process_words(aligned_refs, aligned_hyps)
```

## Thuật toán span merge (chi tiết)

### Input sau Gemini

- `anchors`: danh sách cặp `(ref_index, hyp_index)` đã validate, **sorted** theo `ref_index` tăng dần (và `hyp_index` cũng phải tăng — monotonic).
- `references[0..N)`, `hypotheses[0..M)`

### Bước 1 — Chuẩn bị biên

Thêm **sentinel ảo** để xử lý đầu/cuối:

```
ref_bounds  = [-1] + [a.ref_index for a in anchors] + [N]
hyp_bounds  = [-1] + [a.hyp_index for a in anchors] + [M]
```

Mỗi khoảng `i` xét span:

```
ref_lo, ref_hi = ref_bounds[i] + 1, ref_bounds[i + 1]   # nửa mở [lo, hi)
hyp_lo, hyp_hi = hyp_bounds[i] + 1, hyp_bounds[i + 1]
```

Số câu trong span: `n_ref = ref_hi - ref_lo`, `n_hyp = hyp_hi - hyp_lo`.

### Bước 2 — Quy tắc từng span

| Điều kiện | Hành vi |
|---|---|
| `n_ref == 0` và `n_hyp == 0` | Bỏ qua (span rỗng — giữa 2 anchors kề nhau không có câu giữa) |
| `n_ref == 1` và `n_hyp == 1` | **Giữ 1 cặp** nguyên: `refs[ref_lo]` ↔ `hyps[hyp_lo]` |
| `n_ref >= 1` hoặc `n_hyp >= 1` (lệch hoặc nhiều câu) | **Span merge**: nối tất cả `refs[ref_lo:ref_hi]` (thứ tự gốc, separator `" "`) thành 1 ref; tương tự hyp → **1 cặp** |
| `n_ref == 0` xor `n_hyp == 0` | Vẫn merge phía còn text; phía kia = `""` chỉ khi span đó **chỉ có insertion/deletion thuần** (một phía rỗng). Ghi meta; WER phản ánh I hoặc D — chấp nhận vì không bịa nội dung |

> **Lưu ý:** Trường hợp `n_ref == 0` / `n_hyp == 0` (thừa hoàn toàn một phía giữa 2 mốc) hiếm nếu Gemini đặt anchor tốt. Vẫn hỗ trợ để không crash.

### Bước 3 — Nối chuỗi

```python
merged_ref = " ".join(references[ref_lo:ref_hi]).strip()
merged_hyp = " ".join(hypotheses[hyp_lo:hyp_hi]).strip()
```

- Giữ **thứ tự gốc** trong span.
- Không đảo, không chia nửa câu.
- Empty sau strip chỉ khi span phía đó không có câu / chỉ whitespace.

### Bước 4 — Kết quả

- `aligned_refs`, `aligned_hyps`: cùng length.
- Nếu sau merge **0 cặp** → `400` “no pairs could be aligned”.
- `alignment_meta.merged_spans`: mô tả các span đã gộp (debug / audit).

### Ví dụ

**Input**

```
refs = ["xin chào", "hôm nay trời đẹp", "tôi thích cà phê"]
hyps = ["xin chào", "hôm nay trời", "đẹp quá", "tôi thích trà"]
```

Gemini anchors (ví dụ): `(0,0)`, `(2,3)` — câu giữa lệch segmentation.

**Spans**

| Span | ref range | hyp range | Action |
|---|---|---|---|
| đầu → anchor0 | `[0,0]` / `[0,0]` | 1-1 | giữ `"xin chào"` ↔ `"xin chào"` |
| giữa 0→2 | `[1,2)` / `[1,3)` | lệch 1 vs 2 | merge `"hôm nay trời đẹp"` ↔ `"hôm nay trời đẹp quá"` |
| anchor2 → cuối | `[2,3)` / `[3,4)` | 1-1 | giữ `"tôi thích cà phê"` ↔ `"tôi thích trà"` |

→ 3 cặp đồng length → jiwer.

## Vai trò Gemini (anchors, không phải drop)

Gemini **không** quyết định drop/pad. Chỉ tìm **mốc khớp semantic** ổn định (anchors), ưu tiên:

- Monotonic (không cross)
- Phủ càng nhiều mốc chắc càng tốt
- Câu không chắc → **không** ép thành anchor (để span merge gộp vào vùng lệch)

### System / instruction

- Vai trò: chuyên gia alignment transcript ASR
- Nhiệm vụ: chọn các cặp **anchor** 1-1 chắc chắn (semantic, VI + EN)
- Mỗi ref/hyp index dùng tối đa 1 lần; thứ tự monotonic
- Không cần cover hết câu — câu còn lại sẽ vào span merge
- Trả JSON thuần / structured output

### User payload

```json
{
  "references": [{"index": 0, "text": "..."}, ...],
  "hypotheses": [{"index": 0, "text": "..."}, ...]
}
```

### Expected Gemini output schema

```json
{
  "anchors": [
    {
      "ref_index": 0,
      "hyp_index": 0,
      "confidence": 0.98,
      "reason": "same greeting"
    },
    {
      "ref_index": 2,
      "hyp_index": 3,
      "confidence": 0.9,
      "reason": "same coffee preference"
    }
  ]
}
```

Dùng **structured output** (`response_mime_type=application/json` + schema).

## Quy tắc validate anchors

1. `ref_index` ∈ `[0, N)`, `hyp_index` ∈ `[0, M)`
2. Không trùng `ref_index` / `hyp_index`
3. Sau sort theo `ref_index`: `hyp_index` phải **không giảm** (monotonic). Vi phạm → loại anchor gây cross (hoặc `502` nếu không sửa được)
4. Confidence ∈ `[0, 1]` (thiếu → mặc định `1.0`); filter theo `GEMINI_MIN_CONFIDENCE`
5. Index lỗi từ Gemini → loại + log warning
6. **0 anchors** vẫn OK nếu `N>=1` hoặc `M>=1`: coi như **một span duy nhất** gộp toàn bộ refs ↔ toàn bộ hyps (document-level pair)
7. Sau merge mà 0 cặp hữu ích (cả hai phía empty) → `400`

## `alignment_meta` (response)

```json
{
  "model": "gemini-2.0-flash",
  "strategy": "span_merge",
  "anchors": [
    {"ref_index": 0, "hyp_index": 0, "confidence": 0.98, "reason": "same greeting"}
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
```

## Fallback khi Gemini fail

| Tình huống | Hành vi |
|---|---|
| Timeout / 5xx Gemini | Retry 2 lần (exponential backoff) → `502` |
| JSON parse fail | 1 lần re-prompt “JSON only” → vẫn fail → `502` |
| `GEMINI_API_KEY` thiếu | `503` ngay |
| 0 anchors (Gemini trả rỗng nhưng HTTP OK) | Span merge **toàn bộ** batch thành 1 cặp (không fail) |
| Optional `alignment=positional` | Chỉ khi `N==M` và client xin skip Gemini (Phase 2 — chưa làm) |

**Không** fallback positional im lặng khi Gemini lỗi mạng/parse.

## Config liên quan

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_RETRIES=2
GEMINI_MIN_CONFIDENCE=0.0
ALIGNMENT_STRATEGY=span_merge
```

## Request flag (API)

Thay `drop_unmatched` bằng (hoặc deprecate):

| Field | Type | Default | Mô tả |
|---|---|---|---|
| `alignment` | string | `"span_merge"` | Chiến lược reconcile. Phase này chỉ hỗ trợ `span_merge`. |

`drop_unmatched` **không dùng** (removed khỏi design mặc định).

## Quyết định đã chốt / còn mở

### Đã chốt

1. **Reconcile lệch câu:** `span_merge` (gộp biên + text lệch → 1 cặp) — không pad, không chia đôi, không drop mặc định.
2. Gemini chỉ trả **anchors**; span merge chạy deterministic sau đó.
3. 0 anchors + HTTP OK → merge cả batch thành 1 cặp.

### Còn duyệt (nhẹ)

1. `GEMINI_MIN_CONFIDENCE` default: **`0.0`** (đề xuất) hay `0.5`?
2. Trả `reason` từ Gemini trong meta: **Có** (đề xuất)?
3. Batch lớn (>50): **1 lần gọi Gemini** (≤100) hay chunk?
4. SDK: **`google-genai`** (đề xuất)?

## Acceptance criteria (Phase 3)

- [x] Thuật toán reconcile lệch câu được chốt: **span_merge**
- [ ] Ngưỡng confidence / reason / chunk / SDK được chốt
- [ ] Fallback & error behavior được chốt (bảng trên)
