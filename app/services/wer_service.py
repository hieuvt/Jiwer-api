"""jiwer wrappers for single and batch WER computation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jiwer


ROUND_DIGITS = 6


def _round_metric(value: float) -> float:
    return round(float(value), ROUND_DIGITS)


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
        return data


def _from_word_output(out: jiwer.WordOutput, *, include_viz: bool = False) -> WerMetrics:
    viz = None
    if include_viz:
        try:
            viz = jiwer.visualize_alignment(out, show_measures=False)
        except Exception:  # noqa: BLE001 — viz is optional
            viz = None
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
    )


def compute_single(
    reference: str,
    hypothesis: str,
    *,
    include_details: bool = True,
) -> dict[str, Any]:
    out = jiwer.process_words(reference, hypothesis)
    metrics = _from_word_output(out, include_viz=include_details)
    payload = metrics.as_dict(include_details=include_details)
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

    overall = jiwer.process_words(references, hypotheses)
    metrics = _from_word_output(overall, include_viz=False)
    payload = metrics.as_dict(include_details=include_details)
    payload["num_pairs"] = len(references)

    if per_pair:
        pairs: list[dict[str, Any]] = []
        for idx, (ref, hyp) in enumerate(zip(references, hypotheses, strict=True)):
            pair_out = jiwer.process_words(ref, hyp)
            pair_metrics = _from_word_output(pair_out, include_viz=False)
            pair_payload = pair_metrics.as_dict(include_details=include_details)
            pair_payload.update(
                {
                    "index": idx,
                    "reference": ref,
                    "hypothesis": hyp,
                }
            )
            pairs.append(pair_payload)
        payload["pairs"] = pairs

    return payload
