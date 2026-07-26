"""Unit tests for wer_service."""

from app.services import wer_service


def test_identical_pair_wer_zero() -> None:
    result = wer_service.compute_single("hello world", "hello world")
    assert result["wer"] == 0.0
    assert result["hits"] == 2


def test_substitution_wer_half() -> None:
    result = wer_service.compute_single("hello world", "hello duck")
    assert result["wer"] == 0.5
    assert result["substitutions"] == 1


def test_vietnamese_near_match() -> None:
    result = wer_service.compute_single("xin chào thế giới", "xin chào thế giới ạ")
    assert result["wer"] > 0
    assert result["wer"] < 1
    assert "insertions" in result


def test_batch_overall_and_pairs() -> None:
    result = wer_service.compute_batch(
        ["hello world", "a b"],
        ["hello world", "a x"],
        include_details=True,
        per_pair=True,
    )
    assert result["num_pairs"] == 2
    assert result["pairs"][0]["wer"] == 0.0
    assert result["pairs"][1]["wer"] == 0.5
