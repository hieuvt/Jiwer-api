"""WER HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    WerBatchRequest,
    WerBatchResponse,
    WerSingleRequest,
    WerSingleResponse,
    AlignmentMeta,
    AnchorMeta,
    MergedSpanMeta,
)
from app.config import Settings, get_settings
from app.services import wer_service
from app.services.gemini_aligner import GeminiAligner

router = APIRouter(prefix="/api/v1", tags=["wer"])


@router.post("/wer", response_model=WerSingleResponse)
def compute_wer_single(body: WerSingleRequest) -> WerSingleResponse:
    try:
        result = wer_service.compute_single(
            body.reference,
            body.hypothesis,
            include_details=body.include_details,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"WER computation failed: {exc}") from exc
    return WerSingleResponse(**result)


@router.post("/wer/batch", response_model=WerBatchResponse)
def compute_wer_batch(
    body: WerBatchRequest,
    settings: Settings = Depends(get_settings),
) -> WerBatchResponse:
    if len(body.references) > settings.max_batch_size or len(body.hypotheses) > settings.max_batch_size:
        raise HTTPException(
            status_code=422,
            detail=f"batch size exceeds max_batch_size={settings.max_batch_size}",
        )

    # raw = đúng nội dung request (trước align/merge)
    references_raw = list(body.references)
    hypotheses_raw = list(body.hypotheses)

    aligner = GeminiAligner(settings)
    alignment = aligner.align(
        references_raw,
        hypotheses_raw,
        strategy=body.alignment,
    )

    # normalized = sau span_merge, qua transform jiwer — dùng để tính WER
    aligned_refs = list(alignment.aligned_refs)
    aligned_hyps = list(alignment.aligned_hyps)

    try:
        metrics = wer_service.compute_batch(
            aligned_refs,
            aligned_hyps,
            include_details=body.include_details,
            per_pair=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"WER computation failed: {exc}") from exc

    raw_pairs = metrics.get("pairs") or []
    references_normalized: list[str] = []
    hypotheses_normalized: list[str] = []
    pair_wers: list[float] = []
    for pair in raw_pairs:
        references_normalized.append(pair.get("reference_normalized") or "")
        hypotheses_normalized.append(pair.get("hypothesis_normalized") or "")
        pair_wers.append(float(pair["wer"]))

    if len(references_normalized) != len(aligned_refs):
        references_normalized = [wer_service.normalize_text(r) for r in aligned_refs]
        hypotheses_normalized = [wer_service.normalize_text(h) for h in aligned_hyps]

    alignment_meta = None
    if body.include_alignment_meta:
        meta = alignment.meta_dict()
        alignment_meta = AlignmentMeta(
            model=meta["model"],
            strategy=meta["strategy"],
            anchors=[AnchorMeta(**a) for a in meta["anchors"]],
            merged_spans=[MergedSpanMeta(**s) for s in meta["merged_spans"]],
            num_pairs_after_merge=meta["num_pairs_after_merge"],
            ref_indices_per_pair=[p.ref_indices for p in alignment.pairs],
            hyp_indices_per_pair=[p.hyp_indices for p in alignment.pairs],
            merged_flags=[p.merged for p in alignment.pairs],
        )

    return WerBatchResponse(
        references_raw=references_raw,
        hypotheses_raw=hypotheses_raw,
        references_normalized=references_normalized,
        hypotheses_normalized=hypotheses_normalized,
        pair_wers=pair_wers,
        wer=metrics["wer"],
        num_pairs=metrics["num_pairs"],
        mer=metrics.get("mer") if body.include_details else None,
        wil=metrics.get("wil") if body.include_details else None,
        wip=metrics.get("wip") if body.include_details else None,
        hits=metrics.get("hits") if body.include_details else None,
        substitutions=metrics.get("substitutions") if body.include_details else None,
        insertions=metrics.get("insertions") if body.include_details else None,
        deletions=metrics.get("deletions") if body.include_details else None,
        alignment_meta=alignment_meta,
    )
