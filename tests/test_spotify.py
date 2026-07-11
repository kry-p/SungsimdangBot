import json
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest
import requests

from modules.api_models import SpotifyAlbum, SpotifyAlbumImage, SpotifyArtist, SpotifyExternalUrls, SpotifyTrack
from modules.spotify import SpotifyRateLimitError, SpotifyService
from resources import strings
from tests.conftest import make_message

TRACK_ID = "A" * 22


def _response(payload, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.content = json.dumps(payload).encode()
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    return response


def _track(with_image=True):
    images = [SpotifyAlbumImage(url="https://i.scdn.co/image/test", width=300, height=300)] if with_image else []
    return SpotifyTrack(
        id=TRACK_ID,
        name="좋은 <날>",
        artists=[SpotifyArtist(name="아이유")],
        album=SpotifyAlbum(name="REAL & TEST", release_date="2010-12-09", images=images),
        duration_ms=233_000,
        external_urls=SpotifyExternalUrls(spotify="https://open.spotify.com/track/test"),
    )


def _service(**kwargs):
    return SpotifyService(
        MagicMock(),
        client_id=kwargs.get("client_id", "client"),
        client_secret=kwargs.get("client_secret", "secret"),
    )


class TestTokenManagement:
    @patch("modules.spotify.requests.post")
    def test_token_is_cached(self, mock_post):
        mock_post.return_value = _response({"access_token": "token", "token_type": "Bearer", "expires_in": 3600})
        service = _service()

        assert service._ensure_token() == "token"
        assert service._ensure_token() == "token"
        mock_post.assert_called_once()

    def test_missing_credentials_shows_unavailable_message(self):
        service = _service(client_id="", client_secret="")
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_unavailable_msg)

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_concurrent_401_refreshes_token_once(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "new-token", "expires_in": 3600})
        service = _service()
        service._access_token = "old-token"
        service._token_expires_at = float("inf")
        barrier = threading.Barrier(2)

        def get_response(*args, **kwargs):
            if kwargs["headers"] == {"Authorization": "Bearer old-token"}:
                # 두 worker가 모두 구 토큰으로 401을 받은 뒤 token refresh 경쟁에 진입하게 한다.
                barrier.wait(timeout=2)
                return _response({}, status_code=401)
            return _response(_track().model_dump())

        mock_get.side_effect = get_response

        with ThreadPoolExecutor(max_workers=2) as executor:
            tracks = list(executor.map(lambda _: service.get_track(TRACK_ID), range(2)))

        assert [track.id for track in tracks] == [TRACK_ID, TRACK_ID]
        mock_post.assert_called_once()


class TestSpotifyAPI:
    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_search_tracks(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({"tracks": {"items": [_track().model_dump()]}})
        service = _service()

        tracks = service.search_tracks("아이유 좋은 날")

        assert tracks[0].id == TRACK_ID
        assert mock_get.call_args.kwargs["params"] == {
            "q": "아이유 좋은 날",
            "type": "track",
            "limit": 5,
            "market": "KR",
        }

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_401_refreshes_token_once(self, mock_post, mock_get):
        mock_post.side_effect = [
            _response({"access_token": "old-token", "expires_in": 3600}),
            _response({"access_token": "new-token", "expires_in": 3600}),
        ]
        mock_get.side_effect = [
            _response({}, status_code=401),
            _response(_track().model_dump()),
        ]
        service = _service()

        track = service.get_track(TRACK_ID)

        assert track.id == TRACK_ID
        assert mock_post.call_count == 2
        assert mock_get.call_args_list[1].kwargs["headers"] == {"Authorization": "Bearer new-token"}

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_rate_limit_raises_specific_error(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({}, status_code=429)
        service = _service()

        with pytest.raises(SpotifyRateLimitError):
            service.search_tracks("test")


class TestSearchHandler:
    def test_empty_keyword_shows_help(self):
        service = _service()
        message = make_message("/spotify")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_help_msg)

    def test_no_results(self):
        service = _service()
        service.search_tracks = MagicMock(return_value=[])
        message = make_message("/spotify unknown")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_no_result_msg)

    def test_search_result_contains_links_attribution_and_callbacks(self):
        service = _service()
        service.search_tracks = MagicMock(return_value=[_track()])
        message = make_message("/spotify 아이유 <좋은 날>")

        service.search_handler(message)

        call = service.bot.reply_to.call_args
        text = call.args[1]
        assert "아이유 &lt;좋은 날&gt;" in text
        assert "좋은 &lt;날&gt;" in text
        assert "https://open.spotify.com/track/test" in text
        assert "콘텐츠 제공: Spotify" in text
        assert call.kwargs["parse_mode"] == "HTML"
        buttons = [button for row in call.kwargs["reply_markup"].keyboard for button in row]
        assert buttons[0].callback_data == f"spotify_track:{TRACK_ID}"

    def test_invalid_track_id_is_excluded(self):
        service = _service()
        track = _track()
        track.id = "A" * 51
        service.search_tracks = MagicMock(return_value=[track])
        message = make_message("/spotify invalid")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_no_result_msg)

    @patch("modules.spotify.requests.post")
    def test_auth_http_error_shows_search_error(self, mock_post):
        mock_post.return_value = _response({}, status_code=500)
        service = _service()
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_error_msg)

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_search_http_error_shows_search_error(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({}, status_code=500)
        service = _service()
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_error_msg)

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_malformed_json_shows_search_error(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({})
        mock_get.return_value.content = b"not-json"
        service = _service()
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_error_msg)


class TestTrackCallback:
    def test_detail_sends_original_artwork_and_open_link(self):
        service = _service()
        service.get_track = MagicMock(return_value=_track())
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        sent = service.bot.send_photo.call_args
        assert sent.args[:2] == (123, "https://i.scdn.co/image/test")
        assert "좋은 &lt;날&gt;" in sent.kwargs["caption"]
        assert "REAL &amp; TEST" in sent.kwargs["caption"]
        button = sent.kwargs["reply_markup"].keyboard[0][0]
        assert button.text == strings.spotify_open_btn
        assert button.url == "https://open.spotify.com/track/test"

    def test_artwork_send_failure_falls_back_to_text(self):
        service = _service()
        service.get_track = MagicMock(return_value=_track())
        service.bot.send_photo.side_effect = Exception("Telegram image fetch failed")
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        service.bot.send_message.assert_called_once()
        assert service.bot.send_message.call_args.args[0] == 123
        assert "콘텐츠 제공: Spotify" in service.bot.send_message.call_args.args[1]

    def test_invalid_callback_is_ignored(self):
        service = _service()
        call = MagicMock()
        call.data = "spotify_track:not-valid"

        service.handle_spotify_callback(call)

        service.bot.send_photo.assert_not_called()
        service.bot.send_message.assert_not_called()


class TestCallbackDetection:
    @pytest.mark.parametrize("value", [f"spotify_track:{TRACK_ID}", "spotify_track:A", "spotify_track:" + "z" * 50])
    def test_spotify_callback(self, value):
        assert SpotifyService.is_spotify_callback(value) is True

    @pytest.mark.parametrize(
        "value",
        [None, "", "spotify", "spotify_track:", "spotify_track:" + "z" * 51, "spotify_track:invalid-id"],
    )
    def test_non_spotify_callback(self, value):
        assert SpotifyService.is_spotify_callback(value) is False
