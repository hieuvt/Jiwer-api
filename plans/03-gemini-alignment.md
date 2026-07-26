# Phase 3 — Gemini Sentence Alignment

## Vấn đề

jiwer batch yêu cầu:

```python
len(references) == len(hypotheses)
# và references[i] tương ứng hypotheses[i]
```

Trong thực tế, ASR output có thể:

- **Lệch thứ tự** so với transcript gốc
- **Thừa / thiếu** câu (merge/split, hallucination, bỏ sót)
- **Nội dung gần giống** nhưng wording khác → cần semantic match, không chỉ exact string

→ Dùng **Gemini** để tạo mapping 1-1 trước khi gọi jiwer.

## Luồng align

```
references[N], hypotheses[M]
        │
        ▼
  Build prompt (index-based)
        │
        ▼
  Gemini generate (JSON mode / response_schema)
        │
        ▼
  Parse → mappings[{ref_index, hyp_index, confidence}]
        │
        ▼
  Validate: indices hợp lệ, không trùng (bijection-ish)
        │
        ├── drop_unmatched=true  → giữ chỉ cặp matched; unmatched ghi vào meta
        └── drop_unmatched=false → nếu còn unmatched hoặc len lệch → 400
        │
        ▼
  aligned_refs[], aligned_hyps[]  (cùng length)
        │
        ▼
  jiwer.process_words(aligned_refs, aligned_hyps)
```

## Prompt strategy (đề xuất)

### System / instruction

- Vai trò: chuyên gia alignment transcript ASR
- Nhiệm vụ: ghép mỗi reference với **nhiều nhất 1** hypothesis gần nghĩa nhất
- Mỗi hypothesis chỉ dùng **1 lần**
- Trả **JSON thuần**, không markdown
- Ưu tiên semantic similarity (tiếng Việt + English)
- Nếu không có cặp đủ tốt (dưới ngưỡng), để unmatched

### User payload shape gửi Gemini

```json
{
  "references": [{"index": 0, "text": "..."}, ...],
  "hypotheses": [{"index": 0, "text": "..."}, ...]
}
```

### Expected Gemini output schema

```json
{
  "mappings": [
    {
      "ref_index": 0,
      "hyp_index": 2,
      "confidence": 0.95,
      "reason": "same greeting content"
    }
  ],
  "unmatched_references": [3],
  "unmatched_hypotheses": [1]
}
```

Dùng **structured output** (`response_mime_type=application/json` + schema) để giảm parse error.

## Quy tắc validate sau Gemini

1. `ref_index` ∈ `[0, N)`, `hyp_index` ∈ `[0, M)`
2. Không trùng `ref_index` / `hyp_index` trong mappings
3. Confidence ∈ `[0, 1]` (nếu thiếu → mặc định `null` hoặc `1.0`)
4. Nếu Gemini trả index lỗi → loại mapping đó + log warning
5. Sau validate:
   - `aligned_count = len(mappings)`
   - Nếu `aligned_count == 0` → `400` “no pairs could be aligned”
   - Nếu `drop_unmatched=false` và (`unmatched_refs` hoặc `unmatched_hyps` khác rỗng) → `400` kèm meta (hoặc chỉ fail khi lệch length sau align — **cần duyệt**)

## Fallback khi Gemini fail

| Tình huống | Hành vi đề xuất |
|---|---|
| Timeout / 5xx Gemini | Retry 2 lần (exponential backoff) → `502` |
| JSON parse fail | 1 lần re-prompt “fix only” → vẫn fail → `502` |
| `GEMINI_API_KEY` thiếu | `503` ngay, không gọi network |
| `N == M` và client muốn skip? | (Optional) mode `alignment=positional` — Phase 2 Q4 |

**Không** fallback positional im lặng khi Gemini fail (tránh WER sai lệch nghiêm trọng). Fail rõ ràng hơn.

## Config liên quan

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_RETRIES=2
GEMINI_MIN_CONFIDENCE=0.0   # filter mapping dưới ngưỡng (0 = không filter)
```

## Quyết định cần duyệt

1. Khi `drop_unmatched=false` và vẫn còn unmatched: **reject 400** hay **vẫn tính trên cặp matched + cảnh báo**?
2. Ngưỡng `GEMINI_MIN_CONFIDENCE` mặc định: `0.0` (nhận hết) hay `0.5`?
3. Có trả `reason` từ Gemini trong response không (debug hữu ích nhưng dài hơn)?
4. Batch lớn (>50): gửi 1 lần Gemini hay chunk (ví dụ 25 cặp/lần) rồi merge?
5. SDK: `google-genai` (mới) hay `google-generativeai` (cũ)? → đề xuất **`google-genai`**.

## Acceptance criteria (Phase 3)

- [ ] Quy tắc match / unmatched được chốt
- [ ] Fallback & error behavior được chốt
- [ ] Model + SDK được chốt
