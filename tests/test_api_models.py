from modules.api_models import (
    KakaoSearchDocument,
    KakaoSearchResponse,
    LaftelAnime,
    LaftelSearchResponse,
    RssfEntry,
    RssfResponse,
)


def test_list_defaults_are_independent():
    first_search = KakaoSearchResponse()
    second_search = KakaoSearchResponse()
    first_search.documents.append(KakaoSearchDocument(title="first"))
    assert second_search.documents == []

    first_anime = LaftelAnime()
    second_anime = LaftelAnime()
    first_anime.genres.append("action")
    assert second_anime.genres == []

    first_laftel = LaftelSearchResponse()
    second_laftel = LaftelSearchResponse()
    first_laftel.results.append(LaftelAnime(id=1))
    assert second_laftel.results == []

    first_rssf = RssfResponse()
    second_rssf = RssfResponse()
    first_rssf.entries.append(RssfEntry(title="first"))
    assert second_rssf.entries == []
