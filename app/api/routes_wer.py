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

    aligner = GeminiAligner(settings)
    alignment = aligner.align(
        body.references,
        body.hypotheses,
        strategy=body.alignment,
    )

    refs_original = list(alignment.aligned_refs)
    hyps_original = list(alignment.aligned_hyps)

    try:
        metrics = wer_service.compute_batch(
            refs_original,
            hyps_original,
            include_details=body.include_details,
            per_pair=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"WER computation failed: {exc}") from exc

    raw_pairs = metrics.get("pairs") or []
    refs_normalized: list[str] = []
    hyps_normalized: list[str] = []
    pair_wers: list[float] = []
    for raw in raw_pairs:
        refs_normalized.append(raw.get("reference_normalized") or "")
        hyps_normalized.append(raw.get("hypothesis_normalized") or "")
        pair_wers.append(float(raw["wer"]))

    # Prefer explicit normalize arrays from originals if pair list missing
    if len(refs_normalized) != len(refs_original):
        refs_normalized = [wer_service.normalize_text(r) for r in refs_original]
        hyps_normalized = [wer_service.normalize_text(h) for h in hyps_original]

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
        references_original=refs_original,
        hypotheses_original=hyps_original,
        references_normalized=refs_normalized,
        hypotheses_normalized=hyps_normalized,
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
