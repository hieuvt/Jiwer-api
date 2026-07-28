"""API tests for single and batch WER endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import wer_service
from app.services.gemini_aligner import AlignmentResult, AlignedPair, Anchor, MergedSpan

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_single_wer() -> None:
    response = client.post(
        "/api/v1/wer",
        json={"reference": "hello world", "hypothesis": "hello duck"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["wer"] == 0.5
    assert body["substitutions"] == 1


def test_single_rejects_empty() -> None:
    response = client.post(
        "/api/v1/wer",
        json={"reference": "", "hypothesis": "hello"},
    )
    assert response.status_code == 422


def test_single_rejects_whitespace() -> None:
    response = client.post(
        "/api/v1/wer",
        json={"reference": "   ", "hypothesis": "hello"},
    )
    assert response.status_code == 422


def test_vietnamese_single() -> None:
    response = client.post(
        "/api/v1/wer",
        json={
            "reference": "tôi thích cà phê",
            "hypothesis": "tôi thích trà",
        },
    )
    assert response.status_code == 200
    assert 0 < response.json()["wer"] <= 1


def test_batch_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    get_settings.cache_clear()
    response = client.post(
        "/api/v1/wer/batch",
        json={
            "references": ["hello world"],
            "hypotheses": ["hello duck"],
        },
    )
    assert response.status_code == 503


def test_batch_with_mocked_aligner() -> None:
    fake = AlignmentResult(
        pairs=[
            AlignedPair("xin chào", "xin chào", [0], [0], False),
            AlignedPair("hôm nay trời đẹp", "hôm nay trời đẹp quá", [1], [1, 2], True),
        ],
        anchors=[Anchor(0, 0, 0.99, "greet")],
        merged_spans=[
            MergedSpan([1], [1, 2], "hôm nay trời đẹp", "hôm nay trời đẹp quá")
        ],
        model="gemini-2.0-flash",
    )
    with patch("app.api.routes_wer.GeminiAligner.align", return_value=fake):
        response = client.post(
            "/api/v1/wer/batch",
            json={
                "references": ["xin chào", "hôm nay trời đẹp"],
                "hypotheses": ["xin chào", "hôm nay trời", "đẹp quá"],
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["num_pairs"] == 2
    # raw = request input (hyp còn 3 câu, chưa merge)
    assert body["references_raw"] == ["xin chào", "hôm nay trời đẹp"]
    assert body["hypotheses_raw"] == ["xin chào", "hôm nay trời", "đẹp quá"]
    # normalized = sau align/merge + jiwer transform (2 cặp)
    assert body["references_normalized"] == [
        wer_service.normalize_text("xin chào"),
        wer_service.normalize_text("hôm nay trời đẹp"),
    ]
    assert body["hypotheses_normalized"] == [
        wer_service.normalize_text("xin chào"),
        wer_service.normalize_text("hôm nay trời đẹp quá"),
    ]
    assert len(body["pair_wers"]) == 2
    assert body["pair_wers"][0] == 0.0
    assert isinstance(body["wer"], float)
    assert body["alignment_meta"]["strategy"] == "span_merge"
    assert body["alignment_meta"]["anchors"][0]["reason"] == "greet"
    assert body["alignment_meta"]["merged_flags"] == [False, True]


def test_batch_rejects_empty_item() -> None:
    response = client.post(
        "/api/v1/wer/batch",
        json={"references": ["hello", ""], "hypotheses": ["hello", "world"]},
    )
    assert response.status_code == 422


def test_batch_max_size(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_BATCH_SIZE", "2")
    get_settings.cache_clear()
    response = client.post(
        "/api/v1/wer/batch",
        json={
            "references": ["a", "b", "c"],
            "hypotheses": ["a", "b", "c"],
        },
    )
    assert response.status_code == 422
