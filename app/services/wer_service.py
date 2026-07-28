"""jiwer wrappers for single and batch WER computation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jiwer


ROUND_DIGITS = 6


def _round_metric(value: float) -> float:
    return round(float(value), ROUND_DIGITS)


def normalize_text(text: str) -> str:
    """Apply jiwer default word transform and join tokens."""
    if text is None:
        return ""
    raw = str(text).strip()
    if not raw:
        return ""
    transformed = jiwer.wer_default(raw)
    if not transformed:
        return ""
    # wer_default(str) -> list[list[str]] with one sentence
    if isinstance(transformed[0], list):
        return " ".join(transformed[0])
    return " ".join(transformed)


@dataclass(slots=True)
class WerMetrics:
    wer: float
    mer: float
    wil: float
    wip: float
    hits: int
    substitutions: int
    insertions: int
    deletions: int
    alignment_viz: str | None = None
    reference_normalized: str | None = None
    hypothesis_normalized: str | None = None

    def as_dict(self, *, include_details: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "wer": _round_metric(self.wer),
            "mer": _round_metric(self.mer),
            "wil": _round_metric(self.wil),
            "wip": _round_metric(self.wip),
        }
        if include_details:
            data.update(
                {
                    "hits": self.hits,
                    "substitutions": self.substitutions,
                    "insertions": self.insertions,
                    "deletions": self.deletions,
                }
            )
            if self.alignment_viz is not None:
                data["alignment_viz"] = self.alignment_viz
        if self.reference_normalized is not None:
            data["reference_normalized"] = self.reference_normalized
        if self.hypothesis_normalized is not None:
            data["hypothesis_normalized"] = self.hypothesis_normalized
        return data


def _from_word_output(
    out: jiwer.WordOutput,
    *,
    include_viz: bool = False,
    original_reference: str | None = None,
    original_hypothesis: str | None = None,
) -> WerMetrics:
    viz = None
    if include_viz:
        try:
            viz = jiwer.visualize_alignment(out, show_measures=False)
        except Exception:  # noqa: BLE001 — viz is optional
            viz = None

    ref_norm = " ".join(out.references[0]) if out.references else ""
    hyp_norm = " ".join(out.hypotheses[0]) if out.hypotheses else ""
    # Fall back for empty originals that jiwer may not process
    if original_reference is not None and not str(original_reference).strip():
        ref_norm = ""
    if original_hypothesis is not None and not str(original_hypothesis).strip():
        hyp_norm = ""

    return WerMetrics(
        wer=out.wer,
        mer=out.mer,
        wil=out.wil,
        wip=out.wip,
        hits=out.hits,
        substitutions=out.substitutions,
        insertions=out.insertions,
        deletions=out.deletions,
        alignment_viz=viz,
        reference_normalized=ref_norm,
        hypothesis_normalized=hyp_norm,
    )


def _process_pair(reference: str, hypothesis: str, *, include_viz: bool = False) -> WerMetrics:
    """Compute metrics for one pair; tolerate one-sided empty after merge."""
    ref = reference if reference is not None else ""
    hyp = hypothesis if hypothesis is not None else ""
    if not str(ref).strip() and not str(hyp).strip():
        return WerMetrics(
            wer=0.0,
            mer=0.0,
            wil=0.0,
            wip=1.0,
            hits=0,
            substitutions=0,
            insertions=0,
            deletions=0,
            reference_normalized="",
            hypothesis_normalized="",
        )
    if not str(ref).strip():
        # Pure insertion: jiwer rejects empty reference — synthesize metrics.
        tokens = normalize_text(hyp).split()
        n = len(tokens) or 1
        return WerMetrics(
            wer=float(n),
            mer=1.0,
            wil=1.0,
            wip=0.0,
            hits=0,
            substitutions=0,
            insertions=len(tokens),
            deletions=0,
            reference_normalized="",
            hypothesis_normalized=normalize_text(hyp),
        )
    if not str(hyp).strip():
        tokens = normalize_text(ref).split()
        n = len(tokens) or 1
        return WerMetrics(
            wer=1.0,
            mer=1.0,
            wil=1.0,
            wip=0.0,
            hits=0,
            substitutions=0,
            insertions=0,
            deletions=len(tokens),
            reference_normalized=normalize_text(ref),
            hypothesis_normalized="",
        )

    out = jiwer.process_words(ref, hyp)
    return _from_word_output(
        out,
        include_viz=include_viz,
        original_reference=ref,
        original_hypothesis=hyp,
    )


def compute_single(
    reference: str,
    hypothesis: str,
    *,
    include_details: bool = True,
) -> dict[str, Any]:
    metrics = _process_pair(reference, hypothesis, include_viz=include_details)
    payload = metrics.as_dict(include_details=include_details)
    payload["reference_raw"] = reference
    payload["hypothesis_raw"] = hypothesis
    payload["reference_normalized"] = metrics.reference_normalized
    payload["hypothesis_normalized"] = metrics.hypothesis_normalized
    # Backward-compatible aliases
    if include_details:
        payload["reference"] = reference
        payload["hypothesis"] = hypothesis
    return payload


def compute_batch(
    references: list[str],
    hypotheses: list[str],
    *,
    include_details: bool = True,
    per_pair: bool = True,
) -> dict[str, Any]:
    if len(references) != len(hypotheses):
        raise ValueError("references and hypotheses must have equal length")
    if not references:
        raise ValueError("references/hypotheses must not be empty")

    # Overall: prefer jiwer list API when no empty strings; else aggregate from pairs.
    if all(str(r).strip() and str(h).strip() for r, h in zip(references, hypotheses, strict=True)):
        overall = jiwer.process_words(references, hypotheses)
        metrics = _from_word_output(overall, include_viz=False)
        payload = metrics.as_dict(include_details=include_details)
    else:
        pair_metrics = [_process_pair(r, h) for r, h in zip(references, hypotheses, strict=True)]
        hits = sum(m.hits for m in pair_metrics)
        substitutions = sum(m.substitutions for m in pair_metrics)
        insertions = sum(m.insertions for m in pair_metrics)
        deletions = sum(m.deletions for m in pair_metrics)
        n_ref_words = hits + substitutions + deletions
        wer = (substitutions + insertions + deletions) / n_ref_words if n_ref_words else 0.0
        payload = {
            "wer": _round_metric(wer),
            "mer": None,
            "wil": None,
            "wip": None,
        }
        if include_details:
            payload.update(
                {
                    "hits": hits,
                    "substitutions": substitutions,
                    "insertions": insertions,
                    "deletions": deletions,
                }
            )

    payload["num_pairs"] = len(references)

    if per_pair:
        pairs: list[dict[str, Any]] = []
        for idx, (ref, hyp) in enumerate(zip(references, hypotheses, strict=True)):
            pair_metrics = _process_pair(ref, hyp, include_viz=False)
            pair_payload = pair_metrics.as_dict(include_details=include_details)
            pair_payload.update(
                {
                    "index": idx,
                    "reference_raw": ref,
                    "hypothesis_raw": hyp,
                    "reference_normalized": pair_metrics.reference_normalized,
                    "hypothesis_normalized": pair_metrics.hypothesis_normalized,
                    # aliases
                    "reference": ref,
                    "hypothesis": hyp,
                }
            )
            pairs.append(pair_payload)
        payload["pairs"] = pairs

    return payload
