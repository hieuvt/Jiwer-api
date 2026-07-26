"""WER HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    WerBatchRequest,
    WerBatchResponse,
    WerPairResult,
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

    aligner = GeminiAligner(settings)
    alignment = aligner.align(
        body.references,
        body.hypotheses,
        strategy=body.alignment,
    )

    try:
        metrics = wer_service.compute_batch(
            alignment.aligned_refs,
            alignment.aligned_hyps,
            include_details=body.include_details,
            per_pair=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"WER computation failed: {exc}") from exc

    pairs_out: list[WerPairResult] = []
    raw_pairs = metrics.pop("pairs", [])
    for aligned, raw in zip(alignment.pairs, raw_pairs, strict=True):
        pairs_out.append(
            WerPairResult(
                index=raw["index"],
                reference=aligned.reference,
                hypothesis=aligned.hypothesis,
                ref_indices=aligned.ref_indices,
                hyp_indices=aligned.hyp_indices,
                merged=aligned.merged,
                wer=raw.get("wer"),
                mer=raw.get("mer") if body.include_details else None,
                wil=raw.get("wil") if body.include_details else None,
                wip=raw.get("wip") if body.include_details else None,
                hits=raw.get("hits") if body.include_details else None,
                substitutions=raw.get("substitutions") if body.include_details else None,
                insertions=raw.get("insertions") if body.include_details else None,
                deletions=raw.get("deletions") if body.include_details else None,
            )
        )

    alignment_meta = None
    if body.include_alignment_meta:
        meta = alignment.meta_dict()
        alignment_meta = AlignmentMeta(
            model=meta["model"],
            strategy=meta["strategy"],
            anchors=[AnchorMeta(**a) for a in meta["anchors"]],
            merged_spans=[MergedSpanMeta(**s) for s in meta["merged_spans"]],
            num_pairs_after_merge=meta["num_pairs_after_merge"],
        )

    return WerBatchResponse(
        wer=metrics["wer"],
        mer=metrics.get("mer"),
        wil=metrics.get("wil"),
        wip=metrics.get("wip"),
        hits=metrics.get("hits") if body.include_details else None,
        substitutions=metrics.get("substitutions") if body.include_details else None,
        insertions=metrics.get("insertions") if body.include_details else None,
        deletions=metrics.get("deletions") if body.include_details else None,
        num_pairs=metrics["num_pairs"],
        pairs=pairs_out if body.include_details else pairs_out,
        alignment_meta=alignment_meta,
    )
