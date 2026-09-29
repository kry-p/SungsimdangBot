import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
import requests
from pydantic import ValidationError

from config import config
from modules.api_models import CodexResetForecastResponse, CodexResetHistoryResponse
from modules.codex_reset import CodexResetService


def _forecast_response():
    return {
        "calculatedAt": "2026-09-26T01:20:00.000Z",
        "validUntil": "2026-09-26T02:05:00.000Z",
        "publicationState": "hinted",
        "displayMode": "probability",
        "answer": {
            "state": "forecast",
            "headline": "64% chance of a Codex reset within 48 hours",
            "secondLine": "39% within 24 hours.",
        },
        "probabilities": {"h24": {"display": 39}, "h48": {"display": 64}},
        "latestReset": {
            "status": "completed",
            "occurredAt": "2026-09-12T08:09:17.000Z",
            "confirmedAt": "2026-09-12T08:20:00.000Z",
        },
        "recordFacts": {"latestConfirmedBroadResetAt": "2026-09-12T08:09:17.000Z"},
    }


def _announced_forecast_response():
    return {
        "calculatedAt": "2026-09-29T07:12:03.460Z",
        "validUntil": "2026-09-29T07:57:03.460Z",
        "publicationState": "announced",
        "displayMode": "probability",
        "answer": {
            "state": "scheduled",
            "headline": "Codex reset announced; time not given",
            "secondLine": "Nothing has changed on your account yet. 41% within 48 hours. 23% within 24 hours.",
        },
        "probabilities": {"h24": {"display": 23}, "h48": {"display": 41}},
        "latestReset": {
            "status": "announced",
            "occurredAt": None,
            "confirmedAt": None,
        },
        "recordFacts": {"latestConfirmedBroadResetAt": "2026-09-26T17:15:02.442Z"},
    }


def _unavailable_forecast_response():
    return {
        "publicationState": "unavailable",
        "answer": {
            "state": "unavailable",
            "headline": "Forecast unavailable",
            "secondLine": "No current probability is available.",
        },
        "probabilities": None,
        "latestReset": None,
    }


def _history_response():
    return {
        "items": [
            {
                "id": "old-banked",
                "announcedAt": "2026-09-03T23:12:09.000Z",
                "kind": "banked",
                "eventKind": "policy_change",
                "status": "recorded",
            },
            {
                "id": "completed-global",
                "announcedAt": "2026-09-12T08:09:17.000Z",
                "kind": "special_global",
                "eventKind": "completed",
                "status": "completed",
                "scope": "all",
            },
            {
                "id": "missed-notice",
                "announcedAt": "2026-09-22T04:31:32.000Z",
                "kind": "special_global",
                "eventKind": "scheduled",
                "status": "missed",
                "scope": "all",
            },
            {
                "id": "new-banked",
                "announcedAt": "2026-09-22T18:23:37.000Z",
                "kind": "banked",
                "eventKind": "policy_change",
                "status": "recorded",
            },
            {
                "id": "active-notice",
                "announcedAt": "2026-09-26T00:07:13.000Z",
                "kind": "special_global",
                "eventKind": "intent",
                "status": "active",
                "scope": "all",
                "evidenceUrl": "/evidence/95a0a970-fd44-4b12-a4d8-d01919074777/",
            },
        ]
    }


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast(mock_get):
    response = MagicMock()
    response.text = json.dumps(_forecast_response())
    mock_get.return_value = response

    forecast = CodexResetService.fetch_forecast()

    mock_get.assert_called_once_with(config.CODEX_RESET_FORECAST_URL, timeout=10)
    response.raise_for_status.assert_called_once_with()
    assert forecast.probabilities.h24.display == 39
    assert forecast.latest_reset.occurred_at.isoformat() == "2026-09-12T08:09:17+00:00"
    assert forecast.latest_reset.confirmed_at.isoformat() == "2026-09-12T08:20:00+00:00"
    assert forecast.answer.second_line == "39% within 24 hours."


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_accepts_announced_reset_without_occurred_at(mock_get):
    response = MagicMock()
    response.text = json.dumps(_announced_forecast_response())
    mock_get.return_value = response

    forecast = CodexResetService.fetch_forecast()

    assert forecast.latest_reset.status == "announced"
    assert forecast.latest_reset.occurred_at is None
    assert forecast.answer.state == "scheduled"
    assert CodexResetService.get_last_confirmed_reset_at(forecast).isoformat() == "2026-09-26T17:15:02.442000+00:00"


@pytest.mark.parametrize("error", [requests.Timeout, requests.HTTPError])
@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_propagates_request_errors(mock_get, error):
    if error is requests.Timeout:
        mock_get.side_effect = error
    else:
        mock_get.return_value.raise_for_status.side_effect = error

    with pytest.raises(error):
        CodexResetService.fetch_forecast()


@patch("modules.codex_reset.requests.get")
def test_fetch_forecast_rejects_invalid_response(mock_get):
    mock_get.return_value.text = json.dumps({"calculatedAt": "2026-09-26T01:20:00.000Z"})

    with pytest.raises(ValidationError):
        CodexResetService.fetch_forecast()


def test_build_forecast_message_shows_probability_before_last_reset_in_kst():
    forecast = CodexResetForecastResponse.model_validate(_forecast_response())
    now = datetime.fromisoformat("2026-09-26T01:30:00+00:00")

    with patch.object(config, "TIMEZONE", ZoneInfo("UTC")):
        message = CodexResetService.build_forecast_message(forecast, now=now)

    assert message == ("• 24시간 이내 전체 초기화 확률 39%\n• 마지막 전체 초기화 2026-09-12 17:09")


@pytest.mark.parametrize("stale", ["expired", "publication_state", "missing_probabilities", "missing_valid_until"])
def test_build_forecast_message_hides_unavailable_probability(stale):
    data = _forecast_response()
    if stale == "publication_state":
        data["publicationState"] = "stale"
    if stale == "missing_probabilities":
        data["probabilities"] = None
    if stale == "missing_valid_until":
        data["validUntil"] = None
    forecast = CodexResetForecastResponse.model_validate(data)
    now = datetime.fromisoformat("2026-09-26T02:10:00+00:00" if stale == "expired" else "2026-09-26T01:30:00+00:00")

    message = CodexResetService.build_forecast_message(forecast, now=now)

    assert "• 24시간 이내 전체 초기화 확률 확인할 수 없음" in message


def test_build_forecast_message_handles_unavailable_snapshot():
    forecast = CodexResetForecastResponse.model_validate(_unavailable_forecast_response())

    message = CodexResetService.build_forecast_message(forecast)

    assert "• 24시간 이내 전체 초기화 확률 확인할 수 없음" in message
    assert "• 마지막 전체 초기화 확인할 수 없음" in message
    assert forecast.calculated_at is None
    assert forecast.valid_until is None
    assert forecast.display_mode is None
    assert forecast.answer.state == "unavailable"


def test_build_forecast_message_uses_confirmed_record_for_announced_reset():
    forecast = CodexResetForecastResponse.model_validate(_announced_forecast_response())
    now = datetime.fromisoformat("2026-09-29T07:30:00+00:00")

    message = CodexResetService.build_forecast_message(forecast, now=now)

    assert message == ("• 24시간 이내 전체 초기화 확률 23%\n• 마지막 전체 초기화 2026-09-27 02:15")


def test_build_forecast_message_handles_missing_last_reset():
    data = _forecast_response()
    data["latestReset"] = None
    data["recordFacts"] = None
    forecast = CodexResetForecastResponse.model_validate(data)

    message = CodexResetService.build_forecast_message(
        forecast,
        now=datetime.fromisoformat("2026-09-26T01:30:00+00:00"),
    )

    assert "• 마지막 전체 초기화 확인할 수 없음" in message


def test_last_confirmed_reset_falls_back_to_occurred_at_without_record_facts():
    data = _forecast_response()
    data["recordFacts"] = None
    forecast = CodexResetForecastResponse.model_validate(data)

    last_reset_at = CodexResetService.get_last_confirmed_reset_at(forecast)

    assert last_reset_at.isoformat() == "2026-09-12T08:09:17+00:00"


@patch("modules.codex_reset.requests.get")
def test_fetch_history(mock_get):
    response = MagicMock()
    response.text = json.dumps(_history_response())
    mock_get.return_value = response

    history = CodexResetService.fetch_history()

    mock_get.assert_called_once_with(config.CODEX_RESET_HISTORY_URL, timeout=10)
    response.raise_for_status.assert_called_once_with()
    assert len(history.items) == 5
    assert history.items[-1].scope == "all"
    assert history.items[-1].evidence_url == "/evidence/95a0a970-fd44-4b12-a4d8-d01919074777/"


@patch("modules.codex_reset.requests.get")
def test_fetch_history_rejects_missing_items(mock_get):
    mock_get.return_value.text = "{}"

    with pytest.raises(ValidationError):
        CodexResetService.fetch_history()


def test_find_latest_active_notice_skips_completed_and_missed_events():
    history = CodexResetHistoryResponse.model_validate(_history_response())
    last_reset_at = datetime.fromisoformat("2026-09-12T08:09:17+00:00")

    notice = CodexResetService.find_latest_active_notice(history, last_reset_at)

    assert notice.id == "active-notice"
    assert CodexResetService.build_active_notice_message(notice) == (
        "• 전체 초기화 예고 (Global Reset Notice)\n"
        "  발표 시각 2026-09-26 09:07\n"
        "  [예고 원문 (Original Notice)](https://resetbeacon.com/evidence/95a0a970-fd44-4b12-a4d8-d01919074777/)\n\n"
    )


def test_active_scheduled_notice_does_not_show_day_deadline_as_reset_time():
    data = _history_response()
    data["items"][-1]["eventKind"] = "scheduled"
    data["items"][-1]["targetAt"] = "2026-09-27T07:00:00.000Z"
    history = CodexResetHistoryResponse.model_validate(data)
    last_reset_at = datetime.fromisoformat("2026-09-12T08:09:17+00:00")

    notice = CodexResetService.find_latest_active_notice(history, last_reset_at)

    assert CodexResetService.build_active_notice_message(notice) == (
        "• 전체 초기화 예고 (Global Reset Notice)\n"
        "  발표 시각 2026-09-26 09:07\n"
        "  [예고 원문 (Original Notice)](https://resetbeacon.com/evidence/95a0a970-fd44-4b12-a4d8-d01919074777/)\n\n"
    )


@pytest.mark.parametrize("scope", ["plus_pro", "model", "unknown", None])
def test_find_latest_active_notice_ignores_non_global_scopes(scope):
    data = _history_response()
    if scope is None:
        del data["items"][-1]["scope"]
    else:
        data["items"][-1]["scope"] = scope
    history = CodexResetHistoryResponse.model_validate(data)

    notice = CodexResetService.find_latest_active_notice(history, None)

    assert notice is None


@pytest.mark.parametrize("evidence_url", [None, "https://example.com/evidence/123/", "/evidence/123/)oops"])
def test_active_notice_omits_missing_or_unsafe_evidence_link(evidence_url):
    data = _history_response()
    data["items"][-1]["evidenceUrl"] = evidence_url
    history = CodexResetHistoryResponse.model_validate(data)

    notice = CodexResetService.find_latest_active_notice(history, None)

    assert CodexResetService.build_active_notice_message(notice) == (
        "• 전체 초기화 예고 (Global Reset Notice)\n  발표 시각 2026-09-26 09:07\n\n"
    )


def test_find_latest_active_notice_ignores_notice_before_last_reset():
    history = CodexResetHistoryResponse.model_validate(_history_response())
    last_reset_at = datetime.fromisoformat("2026-09-27T00:00:00+00:00")

    notice = CodexResetService.find_latest_active_notice(history, last_reset_at)

    assert notice is None
    assert CodexResetService.build_active_notice_message(notice) == ""


def test_find_latest_banked_update_uses_newest_announcement():
    history = CodexResetHistoryResponse.model_validate(_history_response())

    update = CodexResetService.find_latest_banked_update(history)

    assert update.id == "new-banked"
    assert CodexResetService.build_banked_updates_message(update) == (
        "\n\n🎟️ Codex 초기화권 정보 (Banked Reset)\n\n• 최근 발표 (Latest Announcement)\n  2026-09-23 03:23"
    )


def test_find_latest_banked_update_ignores_superseded_announcement():
    data = _history_response()
    data["items"].append(
        {
            "id": "superseded-banked",
            "announcedAt": "2026-09-24T00:00:00.000Z",
            "kind": "banked",
            "eventKind": "policy_change",
            "status": "superseded",
        }
    )
    history = CodexResetHistoryResponse.model_validate(data)

    update = CodexResetService.find_latest_banked_update(history)

    assert update.id == "new-banked"


def test_find_latest_banked_update_returns_none_for_only_superseded_announcements():
    history = CodexResetHistoryResponse.model_validate(
        {
            "items": [
                {
                    "id": "superseded-banked",
                    "announcedAt": "2026-09-24T00:00:00.000Z",
                    "kind": "banked",
                    "eventKind": "policy_change",
                    "status": "superseded",
                }
            ]
        }
    )

    assert CodexResetService.find_latest_banked_update(history) is None


def test_build_banked_updates_message_handles_missing_update():
    assert CodexResetService.build_banked_updates_message(None) == (
        "\n\n🎟️ Codex 초기화권 정보 (Banked Reset)\n\n• 확인할 수 없음"
    )
