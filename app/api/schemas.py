"""Request/response schemas for WER API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _reject_blank(value: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError("must be a non-empty string")
    return value


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    version: str = Field(examples=["0.1.0"])


class WerSingleRequest(BaseModel):
    reference: str
    hypothesis: str
    include_details: bool = True

    @field_validator("reference", "hypothesis")
    @classmethod
    def non_empty(cls, value: str) -> str:
        return _reject_blank(value)


class WerSingleResponse(BaseModel):
    wer: float
    reference_raw: str | None = None
    reference_normalized: str | None = None
    hypothesis_raw: str | None = None
    hypothesis_normalized: str | None = None
    mer: float | None = None
    wil: float | None = None
    wip: float | None = None
    hits: int | None = None
    substitutions: int | None = None
    insertions: int | None = None
    deletions: int | None = None
    reference: str | None = None
    hypothesis: str | None = None
    alignment_viz: str | None = None


class WerBatchRequest(BaseModel):
    references: list[str] = Field(min_length=1)
    hypotheses: list[str] = Field(min_length=1)
    include_details: bool = True
    include_alignment_meta: bool = True
    alignment: Literal["span_merge"] = "span_merge"

    @field_validator("references", "hypotheses")
    @classmethod
    def non_empty_items(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("must contain at least one item")
        return [_reject_blank(v) for v in values]


class AnchorMeta(BaseModel):
    ref_index: int
    hyp_index: int
    confidence: float | None = None
    reason: str | None = None


class MergedSpanMeta(BaseModel):
    ref_indices: list[int]
    hyp_indices: list[int]
    merged_reference: str
    merged_hypothesis: str


class AlignmentMeta(BaseModel):
    model: str
    strategy: str
    anchors: list[AnchorMeta]
    merged_spans: list[MergedSpanMeta]
    num_pairs_after_merge: int
    ref_indices_per_pair: list[list[int]] | None = None
    hyp_indices_per_pair: list[list[int]] | None = None
    merged_flags: list[bool] | None = None


class WerBatchResponse(BaseModel):
    """Batch WER response.

    - ``*_raw``: đúng mảng request (trước align/merge), có thể lệch độ dài.
    - ``*_normalized``: sau span_merge + transform jiwer (cùng độ dài, dùng tính WER).
    - ``pair_wers`` / ``wer``: WER từng cặp và toàn batch trên normalized.
    """

    references_raw: list[str]
    hypotheses_raw: list[str]
    references_normalized: list[str]
    hypotheses_normalized: list[str]
    pair_wers: list[float]
    wer: float
    num_pairs: int
    mer: float | None = None
    wil: float | None = None
    wip: float | None = None
    hits: int | None = None
    substitutions: int | None = None
    insertions: int | None = None
    deletions: int | None = None
    alignment_meta: AlignmentMeta | None = None
