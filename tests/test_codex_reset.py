import json
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
import requests
from pydantic import ValidationError

from config import config
from modules.api_models import CodexResetForecastResponse, CodexResetTimelineResponse
from modules.codex_reset import CodexResetService


def _forecast_response():
    return {
        "updated_at": "2026-09-01T12:35:40.496Z",
        "probabilities": {
            "raw_24h": 0.2745,
            "raw_48h": 0.4737,
            "rounded_24h": 25,
            "rounded_48h": 45,
        },
        "confidence": "low",
        "confidence_note": "Experimental forecast",
        "last_reset_at": "2026-08-31T02:34:27.000Z",
        "age_days": 1.4,
        "latest_alert": {
            "id": "2094252447271366730",
            "kind": "reset",
            "state": "confirmed",
            "source_at": "2026-08-31T02:34:27.000Z",
            "summary": "Usage reset confirmed",
            "url": "https://example.com/reset",
            "corrected": True,
        },
    }


def _timeline_response():
    return {
        "updated_at": "2026-09-04T12:22:15.405Z",
        "events": [
            {
                "id": "newer-hard-reset",
                "announced_at": "2026-09-04T01:00:00.000Z",
                "summary": "Global usage reset",
                "url": "https://example.com/hard-reset",
                "reset_kind": "hard",
                "confidence": "high",
            },
            {
                "id": "latest-banked-announcement",
                "announced_at": "2026-09-03T23:12:09.000Z",
                "summary": "New banked reset announcement",
                "url": "https://example.com/latest-banked",
                "reset_kind": "banked",
                "banked_state": "announced",
                "confidence": "medium",
            },
            {
                "id": "available-banked-reset",
                "announced_at": "2026-08-22T00:50:36.000Z",
                "summary": "Banked reset available",
                "url": "https://example.com/available-banked",
                "reset_kind": "banked",
                "banked_state": "available",
                "confidence": "high",
            },
            {
                "id": "older-banked-announcement",
                "announced_at": "2026-08-21T11:43:19.000Z",
                "summary": "Old banked reset announcement",
                "url": "https://example.com/older-banked",
                "reset_kind": "banked",
                "banked_state": "announced",
                "confidence": "high",
            },
        ],
    }


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast(mock_get):
    response = MagicMock()
    response.text = json.dumps(_forecast_response())
    mock_get.return_value = response

    forecast = CodexResetService.fetch_forecast()

    mock_get.assert_called_once_with(
        config.CODEX_RESET_FORECAST_URL,
        timeout=10,
    )
    response.raise_for_status.assert_called_once_with()
    assert forecast.probabilities.rounded_24h == 25
    assert forecast.probabilities.rounded_48h == 45
    assert forecast.confidence == "low"
    assert forecast.age_days == 1.4
    assert forecast.latest_alert is not None
    assert forecast.latest_alert.state == "confirmed"


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_propagates_timeout(mock_get):
    mock_get.side_effect = requests.Timeout

    with pytest.raises(requests.Timeout):
        CodexResetService.fetch_forecast()


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_propagates_http_error(mock_get):
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError
    mock_get.return_value = response

    with pytest.raises(requests.HTTPError):
        CodexResetService.fetch_forecast()


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_rejects_invalid_json(mock_get):
    response = MagicMock()
    response.text = "not-json"
    mock_get.return_value = response

    with pytest.raises(ValidationError):
        CodexResetService.fetch_forecast()


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_rejects_missing_required_fields(mock_get):
    response = MagicMock()
    response.text = json.dumps({"updated_at": "2026-09-01T12:35:40.496Z"})
    mock_get.return_value = response

    with pytest.raises(ValidationError):
        CodexResetService.fetch_forecast()


def test_build_forecast_message_translates_forecast_to_korean():
    forecast = CodexResetForecastResponse.model_validate(_forecast_response())

    with patch.object(config, "TIMEZONE", ZoneInfo("Asia/Seoul")):
        message = CodexResetService.build_forecast_message(forecast)

    assert message.startswith("🎫 Codex 전체 초기화 정보\n\n")
    assert "2026년 8월 31일 11:34 (KST)" in message
    assert "약 1.4일 전" not in message
    assert ("• 24시간 이내 확률: 25%(신뢰도 낮음)\n• 출처: https://example.com/reset") in message
    assert "48시간 이내: 45%" not in message
    assert "• 예측 신뢰도:" not in message
    assert "예측 기준" not in message
    assert "예측 데이터 갱신" not in message
    assert "https://codex-reset.com/" not in message


def test_build_forecast_message_handles_missing_optional_values():
    response_data = _forecast_response()
    response_data.update(
        {
            "confidence": "unexpected",
            "last_reset_at": None,
            "age_days": None,
            "latest_alert": None,
        }
    )
    forecast = CodexResetForecastResponse.model_validate(response_data)

    message = CodexResetService.build_forecast_message(forecast)

    assert "• 최근 초기화: 확인할 수 없음" in message
    assert "경과 시간을 확인할 수 없음" not in message
    assert "24시간 이내 확률: 25%(신뢰도 알 수 없음)" in message
    assert "• 출처: 확인할 수 없음" in message


@pytest.mark.parametrize(
    ("confidence", "expected_label"),
    [
        ("low", "낮음"),
        ("medium", "보통"),
        ("high", "높음"),
    ],
)
def test_build_forecast_message_translates_known_confidence_levels(confidence, expected_label):
    response_data = _forecast_response()
    response_data["confidence"] = confidence
    forecast = CodexResetForecastResponse.model_validate(response_data)

    message = CodexResetService.build_forecast_message(forecast)

    assert f"24시간 이내 확률: 25%(신뢰도 {expected_label})" in message


def test_build_forecast_message_uses_configured_timezone():
    forecast = CodexResetForecastResponse.model_validate(_forecast_response())

    with patch.object(config, "TIMEZONE", ZoneInfo("UTC")):
        message = CodexResetService.build_forecast_message(forecast)

    assert "2026년 8월 31일 02:34 (UTC)" in message


@pytest.mark.parametrize(
    ("kind", "state", "url"),
    [
        ("outage", "confirmed", "https://example.com/outage"),
        ("reset", "investigating", "https://example.com/reset"),
        ("reset", "confirmed", ""),
    ],
)
def test_build_forecast_message_hides_unconfirmed_reset_source(kind, state, url):
    response_data = _forecast_response()
    response_data["latest_alert"].update(
        {
            "kind": kind,
            "state": state,
            "url": url,
        }
    )
    forecast = CodexResetForecastResponse.model_validate(response_data)

    message = CodexResetService.build_forecast_message(forecast)

    assert "• 출처: 확인할 수 없음" in message
    if url:
        assert url not in message


@patch("modules.codex_reset.requests.get")
def test_fetch_timeline(mock_get):
    response = MagicMock()
    response.text = json.dumps(_timeline_response())
    mock_get.return_value = response

    timeline = CodexResetService.fetch_timeline()

    mock_get.assert_called_once_with(
        config.CODEX_RESET_TIMELINE_URL,
        timeout=10,
    )
    response.raise_for_status.assert_called_once_with()
    assert len(timeline.events) == 4
    assert timeline.events[1].banked_state == "announced"


@patch("modules.codex_reset.requests.get")
def test_fetch_timeline_propagates_timeout(mock_get):
    mock_get.side_effect = requests.Timeout

    with pytest.raises(requests.Timeout):
        CodexResetService.fetch_timeline()


@patch("modules.codex_reset.requests.get")
def test_fetch_timeline_propagates_http_error(mock_get):
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError
    mock_get.return_value = response

    with pytest.raises(requests.HTTPError):
        CodexResetService.fetch_timeline()


@patch("modules.codex_reset.requests.get")
def test_fetch_timeline_rejects_invalid_json(mock_get):
    response = MagicMock()
    response.text = "not-json"
    mock_get.return_value = response

    with pytest.raises(ValidationError):
        CodexResetService.fetch_timeline()


@patch("modules.codex_reset.requests.get")
def test_fetch_timeline_rejects_missing_required_fields(mock_get):
    response = MagicMock()
    response.text = json.dumps({"events": []})
    mock_get.return_value = response

    with pytest.raises(ValidationError):
        CodexResetService.fetch_timeline()


def test_find_latest_banked_announcement_ignores_other_events():
    timeline = CodexResetTimelineResponse.model_validate(_timeline_response())

    announcement = CodexResetService.find_latest_banked_announcement(timeline)

    assert announcement is not None
    assert announcement.id == "latest-banked-announcement"


def test_find_latest_banked_announcement_returns_none_when_missing():
    response_data = _timeline_response()
    for event in response_data["events"]:
        event["banked_state"] = "available"
    timeline = CodexResetTimelineResponse.model_validate(response_data)

    announcement = CodexResetService.find_latest_banked_announcement(timeline)

    assert announcement is None


def test_build_banked_announcement_message():
    timeline = CodexResetTimelineResponse.model_validate(_timeline_response())
    announcement = CodexResetService.find_latest_banked_announcement(timeline)

    with patch.object(config, "TIMEZONE", ZoneInfo("Asia/Seoul")):
        message = CodexResetService.build_banked_announcement_message(announcement)

    assert message == (
        "\n\n🎟️ Codex 초기화권 정보\n\n"
        "• 최근 발표: 2026년 9월 4일 08:12 (KST)\n"
        "• 출처: https://example.com/latest-banked"
    )
    assert "New banked reset announcement" not in message


def test_build_banked_announcement_message_handles_missing_announcement():
    message = CodexResetService.build_banked_announcement_message(None)

    assert "🎟️ Codex 초기화권 정보" in message
    assert "• 최근 발표: 확인할 수 없음" in message
