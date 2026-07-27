# Sample payloads — POST /api/v1/wer/batch

| File | Mục đích |
|---|---|
| `batch_vi_span_merge.json` | VI, hyp thừa câu giữa (cần span_merge) |
| `batch_vi_reordered.json` | VI, đảo thứ tự câu |
| `batch_en_simple.json` | EN, cùng số câu, gần giống |

## Curl

```bash
# local / server
BASE=http://127.0.0.1:10000
# hoặc: BASE=http://103.141.141.15:10000

curl -sS -X POST "$BASE/api/v1/wer/batch" \
  -H 'Content-Type: application/json' \
  -d @docs/samples/batch_vi_span_merge.json | python3 -m json.tool
```

Cần `GEMINI_API_KEY` trong `.env` (batch sẽ `503` nếu thiếu).
