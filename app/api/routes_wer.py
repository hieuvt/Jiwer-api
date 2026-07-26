"""WER routes — mounted in later phases (single + batch)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["wer"])


# Phase 1+ will add:
#   POST /api/v1/wer
#   POST /api/v1/wer/batch
