import pytest

from modules.api_models import (
    KakaoSearchDocument,
    KakaoSearchResponse,
    LaftelAnime,
    LaftelSearchResponse,
    RssfEntry,
    RssfResponse,
)


@pytest.mark.parametrize(
    "model_cls, field, item",
    [
        (KakaoSearchResponse, "documents", KakaoSearchDocument(title="x")),
        (LaftelAnime, "genres", "action"),
        (LaftelSearchResponse, "results", LaftelAnime(id=1)),
        (RssfResponse, "entries", RssfEntry(title="x")),
    ],
)
def test_list_defaults_are_independent(model_cls, field, item):
    first = model_cls()
    second = model_cls()
    getattr(first, field).append(item)
    assert getattr(second, field) == []
