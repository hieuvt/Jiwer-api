"""Gemini anchor discovery + deterministic span_merge reconciliation."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

from app.config import Settings, get_settings
from app.core.exceptions import AlignmentError, GeminiConfigError, GeminiUnavailableError

logger = logging.getLogger(__name__)

ANCHOR_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "anchors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref_index": {"type": "integer"},
                    "hyp_index": {"type": "integer"},
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["ref_index", "hyp_index"],
            },
        }
    },
    "required": ["anchors"],
}


@dataclass(slots=True)
class Anchor:
    ref_index: int
    hyp_index: int
    confidence: float | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ref_index": self.ref_index,
            "hyp_index": self.hyp_index,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass(slots=True)
class MergedSpan:
    ref_indices: list[int]
    hyp_indices: list[int]
    merged_reference: str
    merged_hypothesis: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ref_indices": self.ref_indices,
            "hyp_indices": self.hyp_indices,
            "merged_reference": self.merged_reference,
            "merged_hypothesis": self.merged_hypothesis,
        }


@dataclass(slots=True)
class AlignedPair:
    reference: str
    hypothesis: str
    ref_indices: list[int]
    hyp_indices: list[int]
    merged: bool


@dataclass(slots=True)
class AlignmentResult:
    pairs: list[AlignedPair]
    anchors: list[Anchor]
    merged_spans: list[MergedSpan]
    model: str
    strategy: str = "span_merge"

    @property
    def aligned_refs(self) -> list[str]:
        return [p.reference for p in self.pairs]

    @property
    def aligned_hyps(self) -> list[str]:
        return [p.hypothesis for p in self.pairs]

    def meta_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "strategy": self.strategy,
            "anchors": [a.as_dict() for a in self.anchors],
            "merged_spans": [s.as_dict() for s in self.merged_spans],
            "num_pairs_after_merge": len(self.pairs),
        }


def validate_and_filter_anchors(
    raw_anchors: list[dict[str, Any]],
    *,
    n_ref: int,
    n_hyp: int,
    min_confidence: float,
) -> list[Anchor]:
    seen_ref: set[int] = set()
    seen_hyp: set[int] = set()
    anchors: list[Anchor] = []

    for item in raw_anchors:
        try:
            ref_i = int(item["ref_index"])
            hyp_i = int(item["hyp_index"])
        except (KeyError, TypeError, ValueError):
            logger.warning("Skipping anchor with invalid indices: %s", item)
            continue

        if not (0 <= ref_i < n_ref and 0 <= hyp_i < n_hyp):
            logger.warning("Skipping out-of-range anchor: %s", item)
            continue
        if ref_i in seen_ref or hyp_i in seen_hyp:
            logger.warning("Skipping duplicate anchor: %s", item)
            continue

        conf_raw = item.get("confidence", 1.0)
        try:
            conf = float(conf_raw) if conf_raw is not None else 1.0
        except (TypeError, ValueError):
            conf = 1.0
        if conf < min_confidence:
            continue

        reason = item.get("reason")
        if reason is not None:
            reason = str(reason)

        anchors.append(Anchor(ref_index=ref_i, hyp_index=hyp_i, confidence=conf, reason=reason))
        seen_ref.add(ref_i)
        seen_hyp.add(hyp_i)

    anchors.sort(key=lambda a: a.ref_index)

    # Enforce monotonic hyp_index; drop anchors that cross.
    filtered: list[Anchor] = []
    last_hyp = -1
    for anchor in anchors:
        if anchor.hyp_index < last_hyp:
            logger.warning("Skipping non-monotonic anchor: %s", anchor)
            continue
        filtered.append(anchor)
        last_hyp = anchor.hyp_index
    return filtered


def _emit_span(
    references: list[str],
    hypotheses: list[str],
    ref_lo: int,
    ref_hi: int,
    hyp_lo: int,
    hyp_hi: int,
    pairs: list[AlignedPair],
    merged_spans: list[MergedSpan],
) -> None:
    """Emit one pair for half-open spans [ref_lo, ref_hi) / [hyp_lo, hyp_hi)."""
    n_r = ref_hi - ref_lo
    n_h = hyp_hi - hyp_lo
    if n_r <= 0 and n_h <= 0:
        return

    ref_indices = list(range(ref_lo, ref_hi))
    hyp_indices = list(range(hyp_lo, hyp_hi))
    merged_ref = " ".join(references[ref_lo:ref_hi]).strip()
    merged_hyp = " ".join(hypotheses[hyp_lo:hyp_hi]).strip()
    if not merged_ref and not merged_hyp:
        return

    is_clean_pair = n_r == 1 and n_h == 1
    if not is_clean_pair:
        merged_spans.append(
            MergedSpan(
                ref_indices=ref_indices,
                hyp_indices=hyp_indices,
                merged_reference=merged_ref,
                merged_hypothesis=merged_hyp,
            )
        )

    pairs.append(
        AlignedPair(
            reference=merged_ref,
            hypothesis=merged_hyp,
            ref_indices=ref_indices,
            hyp_indices=hyp_indices,
            merged=not is_clean_pair,
        )
    )


def span_merge(
    references: list[str],
    hypotheses: list[str],
    anchors: list[Anchor],
) -> tuple[list[AlignedPair], list[MergedSpan]]:
    """Reconcile lists using anchors as 1-1 pairs and span-merging gaps.

    - Head gap (before first anchor) is merged if non-empty on either side.
    - Each anchor is emitted as a clean 1-1 pair.
    - Gap between consecutive anchors is merged if non-empty.
    - Tail gap (after last anchor) is merged if non-empty.
    - Zero anchors → one merged pair over the entire batch.
    """
    n_ref = len(references)
    n_hyp = len(hypotheses)
    pairs: list[AlignedPair] = []
    merged_spans: list[MergedSpan] = []

    if not anchors:
        _emit_span(references, hypotheses, 0, n_ref, 0, n_hyp, pairs, merged_spans)
        if not pairs:
            raise AlignmentError("no pairs could be aligned after span_merge")
        return pairs, merged_spans

    # Head: [0, first_anchor)
    first = anchors[0]
    _emit_span(
        references,
        hypotheses,
        0,
        first.ref_index,
        0,
        first.hyp_index,
        pairs,
        merged_spans,
    )

    for i, anchor in enumerate(anchors):
        # Anchor itself as 1-1
        _emit_span(
            references,
            hypotheses,
            anchor.ref_index,
            anchor.ref_index + 1,
            anchor.hyp_index,
            anchor.hyp_index + 1,
            pairs,
            merged_spans,
        )
        # Gap to next anchor (or tail after loop)
        if i + 1 < len(anchors):
            nxt = anchors[i + 1]
            _emit_span(
                references,
                hypotheses,
                anchor.ref_index + 1,
                nxt.ref_index,
                anchor.hyp_index + 1,
                nxt.hyp_index,
                pairs,
                merged_spans,
            )

    # Tail: after last anchor
    last = anchors[-1]
    _emit_span(
        references,
        hypotheses,
        last.ref_index + 1,
        n_ref,
        last.hyp_index + 1,
        n_hyp,
        pairs,
        merged_spans,
    )

    if not pairs:
        raise AlignmentError("no pairs could be aligned after span_merge")

    return pairs, merged_spans


class GeminiAligner:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def align(
        self,
        references: list[str],
        hypotheses: list[str],
        *,
        strategy: str = "span_merge",
    ) -> AlignmentResult:
        if strategy != "span_merge":
            raise AlignmentError(f"unsupported alignment strategy: {strategy}", status_code=422)

        anchors = self._fetch_anchors(references, hypotheses)
        pairs, merged_spans = span_merge(references, hypotheses, anchors)
        return AlignmentResult(
            pairs=pairs,
            anchors=anchors,
            merged_spans=merged_spans,
            model=self.settings.gemini_model,
            strategy=strategy,
        )

    def _fetch_anchors(self, references: list[str], hypotheses: list[str]) -> list[Anchor]:
        api_key = self.settings.gemini_api_key
        if not api_key:
            raise GeminiConfigError()

        payload = {
            "references": [{"index": i, "text": t} for i, t in enumerate(references)],
            "hypotheses": [{"index": i, "text": t} for i, t in enumerate(hypotheses)],
        }
        instruction = (
            "You are an ASR transcript alignment expert for Vietnamese and English. "
            "Select confident 1-1 semantic anchors between references and hypotheses. "
            "Each ref_index and hyp_index may be used at most once. "
            "Anchors must be monotonic (increasing hyp_index when sorted by ref_index). "
            "You do not need to cover every sentence; uncovered sentences will be "
            "span-merged later. Return JSON only with key 'anchors'."
        )

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=int(self.settings.gemini_timeout_seconds * 1000)
            ),
        )

        last_error: Exception | None = None
        attempts = self.settings.gemini_max_retries + 1
        for attempt in range(attempts):
            try:
                response = client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=(
                        f"{instruction}\n\nInput:\n{json.dumps(payload, ensure_ascii=False)}"
                    ),
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                        response_schema=ANCHOR_RESPONSE_SCHEMA,
                    ),
                )
                text = (response.text or "").strip()
                data = json.loads(text) if text else {"anchors": []}
                raw = data.get("anchors", [])
                if not isinstance(raw, list):
                    raise ValueError("anchors must be a list")
                return validate_and_filter_anchors(
                    raw,
                    n_ref=len(references),
                    n_hyp=len(hypotheses),
                    min_confidence=self.settings.gemini_min_confidence,
                )
            except GeminiConfigError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "Gemini anchor call failed (attempt %s/%s): %s",
                    attempt + 1,
                    attempts,
                    exc,
                )
                if attempt + 1 < attempts:
                    time.sleep(2**attempt)

        raise GeminiUnavailableError(f"Gemini API unavailable: {last_error}")
