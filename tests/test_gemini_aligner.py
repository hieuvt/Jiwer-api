"""Unit tests for span_merge and anchor validation."""

import pytest

from app.core.exceptions import AlignmentError
from app.services.gemini_aligner import (
    Anchor,
    load_system_prompt,
    span_merge,
    validate_and_filter_anchors,
)


def test_load_system_prompt_from_docs() -> None:
    prompt = load_system_prompt()
    assert "ASR transcript alignment" in prompt
    assert "anchors" in prompt.lower()


def test_clean_one_to_one_no_merge() -> None:
    refs = ["xin chào", "tạm biệt"]
    hyps = ["xin chào", "tạm biệt"]
    anchors = [Anchor(0, 0, 1.0, "a"), Anchor(1, 1, 1.0, "b")]
    pairs, merged = span_merge(refs, hyps, anchors)
    assert len(pairs) == 2
    assert merged == []
    assert pairs[0].merged is False


def test_hyp_split_span_merge() -> None:
    refs = ["xin chào", "hôm nay trời đẹp", "tôi thích cà phê"]
    hyps = ["xin chào", "hôm nay trời", "đẹp quá", "tôi thích trà"]
    anchors = [Anchor(0, 0, 0.9, "greet"), Anchor(2, 3, 0.9, "coffee")]
    pairs, merged = span_merge(refs, hyps, anchors)
    assert len(pairs) == 3
    assert len(merged) == 1
    assert pairs[1].merged is True
    assert pairs[1].reference == "hôm nay trời đẹp"
    assert pairs[1].hypothesis == "hôm nay trời đẹp quá"
    assert pairs[1].hyp_indices == [1, 2]


def test_zero_anchors_merges_entire_batch() -> None:
    refs = ["a b", "c d"]
    hyps = ["a b c d"]
    pairs, merged = span_merge(refs, hyps, [])
    assert len(pairs) == 1
    assert pairs[0].merged is True
    assert pairs[0].reference == "a b c d"
    assert pairs[0].hypothesis == "a b c d"
    assert len(merged) == 1


def test_validate_anchors_monotonic_and_range() -> None:
    raw = [
        {"ref_index": 0, "hyp_index": 1, "confidence": 0.9},
        {"ref_index": 1, "hyp_index": 0, "confidence": 0.9},  # crosses
        {"ref_index": 9, "hyp_index": 0, "confidence": 0.9},  # OOR
    ]
    anchors = validate_and_filter_anchors(raw, n_ref=2, n_hyp=2, min_confidence=0.0)
    assert len(anchors) == 1
    assert anchors[0].ref_index == 0


def test_span_merge_both_empty_raises() -> None:
    with pytest.raises(AlignmentError):
        span_merge([], [], [])
