import datetime
import json
import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

from modules.api_models import KakaoSearchDocument, KakaoSearchResponse
from modules.web_based import WebManager
from resources import strings
from tests.conftest import make_message


class TestWebManagerInit:
    @patch("modules.web_based.requests.get")
    @patch("modules.web_based.datetime")
    def test_init_normal_minute(self, mock_dt, mock_get):
        fixed_now = datetime.datetime(2024, 6, 15, 14, 15, 0)
        mock_dt.datetime.now.return_value = fixed_now
        mock_dt.datetime.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)
        mock_dt.timedelta = datetime.timedelta

        response = MagicMock()
        response.text = json.dumps({"WPOSInformationTime": {"row": [{"WATT": "22.0"}]}})
        mock_get.return_value = response

        wm = WebManager()
        assert wm.last_update_time == datetime.datetime(2024, 6, 15, 14, 1)

    @patch("modules.web_based.requests.get")
    @patch("modules.web_based.datetime")
    def test_init_minute_zero(self, mock_dt, mock_get):
        fixed_now = datetime.datetime(2024, 6, 15, 14, 0, 0)
        mock_dt.datetime.now.return_value = fixed_now
        mock_dt.datetime.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)
        mock_dt.timedelta = datetime.timedelta

        response = MagicMock()
        response.text = json.dumps({"WPOSInformationTime": {"row": [{"WATT": "22.0"}]}})
        mock_get.return_value = response

        wm = WebManager()
        assert wm.last_update_time == datetime.datetime(2024, 6, 15, 13, 1)


class TestUpdateSuon:
    @patch("modules.web_based.requests.get")
    def test_success(self, mock_get):
        response = MagicMock()
        response.text = json.dumps({"WPOSInformationTime": {"row": [{"WATT": "22.5"}]}})
        mock_get.return_value = response

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            wm.suon_v2 = None
            wm.last_update_time = datetime.datetime(2020, 1, 1)
            wm.update_suon()
            assert wm.suon_v2 == "22.5"

    @patch("modules.web_based.requests.get")
    def test_api_failure(self, mock_get):
        mock_get.side_effect = Exception("connection error")

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            wm.suon_v2 = None
            wm.last_update_time = datetime.datetime(2020, 1, 1)
            wm.update_suon()
            assert wm.suon_v2 is None

    @patch("modules.web_based.requests.get")
    def test_skip_when_recently_updated(self, mock_get):
        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            wm.suon_v2 = "20.0"
            wm.last_update_time = datetime.datetime.now() - datetime.timedelta(seconds=100)
            wm.update_suon()
            mock_get.assert_not_called()

    @patch("modules.web_based.requests.get")
    def test_refresh_after_over_24_hours(self, mock_get):
        response = MagicMock()
        response.text = json.dumps({"WPOSInformationTime": {"row": [{"WATT": "21.0"}]}})
        mock_get.return_value = response

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            wm.suon_v2 = "20.0"
            wm.last_update_time = datetime.datetime.now() - datetime.timedelta(hours=25)
            wm.update_suon()
            mock_get.assert_called_once()
            assert wm.suon_v2 == "21.0"


class TestDaumSearch:
    @patch("modules.web_based.config.KAKAO_TOKEN", "test_token")
    @patch("modules.web_based.requests.get")
    def test_success(self, mock_get):
        response = MagicMock()
        response.text = json.dumps(
            {"documents": [{"title": "test", "contents": "content", "url": "https://example.com/path"}]}
        )
        mock_get.return_value = response

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/search test")
            result = wm.daum_search(msg, None)
            assert len(result.documents) == 1

    @patch("modules.web_based.config.KAKAO_TOKEN", "test_token")
    @patch("modules.web_based.requests.get")
    def test_empty_result(self, mock_get):
        response = MagicMock()
        response.text = json.dumps({"documents": []})
        mock_get.return_value = response

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/search nothing")
            result = wm.daum_search(msg, None)
            assert result.documents == []

    @patch("modules.web_based.config.KAKAO_TOKEN", "test_token")
    @patch("modules.web_based.requests.get")
    def test_http_error(self, mock_get):
        mock_get.side_effect = Exception("timeout")

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/search fail")
            result = wm.daum_search(msg, None)
            assert result.documents == []


class TestDaumSearchMultiWord:
    @patch("modules.web_based.config.KAKAO_TOKEN", "test_token")
    @patch("modules.web_based.requests.get")
    def test_multi_word_keyword(self, mock_get):
        response = MagicMock()
        response.text = json.dumps(
            {"documents": [{"title": "result", "contents": "content", "url": "https://example.com/path"}]}
        )
        mock_get.return_value = response

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/search hello world today")
            wm.daum_search(msg, None)

            call_url = mock_get.call_args[0][0]
            assert "hello+world+today" in call_url or "hello%20world%20today" in call_url


class TestNamuwikiSearch:
    @patch.object(WebManager, "daum_search")
    def test_normal_result(self, mock_daum):
        mock_daum.return_value = KakaoSearchResponse(
            documents=[KakaoSearchDocument(title="test", contents="<b>content</b>", url="https://namu.wiki/w/test")]
        )

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/namu test")
            result = wm.namuwiki_search(msg)
            assert "나무위키" in result

    @patch.object(WebManager, "daum_search")
    def test_empty_documents(self, mock_daum):
        mock_daum.return_value = KakaoSearchResponse()

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/namu nothing")
            result = wm.namuwiki_search(msg)
            assert result == strings.search_no_result_msg


class TestNamuwikiSearchMultiWord:
    @patch.object(WebManager, "daum_search")
    def test_multi_word_keyword(self, mock_daum):
        encoded = urllib.parse.quote("hello world")
        mock_daum.return_value = KakaoSearchResponse(
            documents=[
                KakaoSearchDocument(
                    title="hello world",
                    contents="<b>some content</b>",
                    url="https://namu.wiki/w/" + encoded,
                )
            ]
        )

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/namu hello world")
            result = wm.namuwiki_search(msg)
            assert "hello world" in result
            assert "나무위키" in result


class TestNamuwikiSearchUrlMismatch:
    @patch.object(WebManager, "daum_search")
    def test_url_mismatch_shows_actual_result(self, mock_daum):
        mock_daum.return_value = KakaoSearchResponse(
            documents=[
                KakaoSearchDocument(
                    title="<b>Different</b> Page",
                    contents="<b>content</b> here",
                    url="https://namu.wiki/w/different_page",
                )
            ]
        )

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/namu test")
            result = wm.namuwiki_search(msg)
            assert strings.search_mismatch_msg.format(keyword="test") in result
            assert "https://namu.wiki/w/different_page" in result
            assert "Different Page" in result
            assert "content here" in result


class TestGeolocationInfo:
    @patch("modules.web_based.config.WEATHER_TOKEN", "test_weather")
    @patch("modules.web_based.config.KAKAO_TOKEN", "test_kakao")
    @patch("modules.web_based.requests.get")
    def test_success(self, mock_get):
        map_response = MagicMock()
        map_response.text = json.dumps({"documents": [{"address": {"address_name": "서울특별시 중구"}}]})

        weather_response = MagicMock()
        weather_response.text = json.dumps(
            {
                "weather": [{"description": "맑음"}],
                "main": {"temp": 293.15, "feels_like": 291.15, "humidity": 50},
            }
        )

        mock_get.side_effect = [map_response, weather_response]

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            result = wm.geolocation_info(37.5, 127.0)
            assert "서울특별시 중구" in result
            assert "맑음" in result
            assert "37.5" in result

    @patch("modules.web_based.config.WEATHER_TOKEN", "test_weather")
    @patch("modules.web_based.config.KAKAO_TOKEN", "test_kakao")
    @patch("modules.web_based.requests.get")
    def test_api_error(self, mock_get):
        mock_get.side_effect = ConnectionError("connection error")

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            with pytest.raises(ConnectionError):
                wm.geolocation_info(37.5, 127.0)


class TestProvideSuonV2:
    def test_none_returns_maintenance(self):
        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            wm.suon_v2 = None
            assert wm.provide_suon_v2() == "점검중"

    def test_normal_value(self):
        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            wm.suon_v2 = "23.5"
            assert wm.provide_suon_v2() == "23.5"
