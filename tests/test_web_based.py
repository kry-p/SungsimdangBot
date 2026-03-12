import datetime
import json
from unittest.mock import MagicMock, patch

from modules.web_based import WebManager
from resources import strings


def make_message(text):
    msg = MagicMock()
    msg.text = text
    return msg


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
            assert len(result["documents"]) == 1

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
            assert result["documents"] == []

    @patch("modules.web_based.config.KAKAO_TOKEN", "test_token")
    @patch("modules.web_based.requests.get")
    def test_http_error(self, mock_get):
        mock_get.side_effect = Exception("timeout")

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/search fail")
            result = wm.daum_search(msg, None)
            assert result == {"documents": []}


class TestNamuwikiSearch:
    @patch.object(WebManager, "daum_search")
    def test_normal_result(self, mock_daum):
        mock_daum.return_value = {
            "documents": [
                {
                    "title": "test",
                    "contents": "<b>content</b>",
                    "url": "https://namu.wiki/w/test",
                }
            ]
        }

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/namu test")
            result = wm.namuwiki_search(msg)
            assert "나무위키" in result

    @patch.object(WebManager, "daum_search")
    def test_empty_documents(self, mock_daum):
        mock_daum.return_value = {"documents": []}

        with patch.object(WebManager, "__init__", lambda self: None):
            wm = WebManager()
            msg = make_message("/namu nothing")
            result = wm.namuwiki_search(msg)
            assert result == strings.search_no_result_msg


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
