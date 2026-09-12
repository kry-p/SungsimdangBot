from datetime import datetime

import requests

from config import config
from modules.api_models import CodexResetForecastResponse, CodexResetTimelineEvent, CodexResetTimelineResponse
from resources import strings

CONFIDENCE_LABELS = {
    "low": "낮음",
    "medium": "보통",
    "high": "높음",
    "unknown": "알 수 없음",
}


class CodexResetService:
    @staticmethod
    def fetch_forecast() -> CodexResetForecastResponse:
        response = requests.get(
            config.CODEX_RESET_FORECAST_URL,
            timeout=10,
        )
        response.raise_for_status()

        forecast = CodexResetForecastResponse.model_validate_json(response.text)

        return forecast

    @staticmethod
    def build_forecast_message(
        forecast: CodexResetForecastResponse,
    ) -> str:
        confidence = CONFIDENCE_LABELS.get(
            forecast.confidence,
            CONFIDENCE_LABELS["unknown"],
        )
        if (
            forecast.latest_alert is not None
            and forecast.latest_alert.kind == "reset"
            and forecast.latest_alert.state == "confirmed"
            and forecast.latest_alert.url
        ):
            source = strings.codex_reset_source_msg.format(
                source_url=forecast.latest_alert.url,
            )
        else:
            source = strings.codex_reset_source_unavailable_msg

        last_reset_at = CodexResetService._format_datetime(
            forecast.last_reset_at,
        )

        return strings.codex_reset_forecast_msg.format(
            last_reset_at=last_reset_at,
            probability_24h=forecast.probabilities.rounded_24h,
            confidence=confidence,
            source=source,
        )

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        if value is None:
            return strings.codex_reset_date_unavailable_msg

        value_local = value.astimezone(config.TIMEZONE)

        return f"{value_local.year}년 {value_local.month}월 {value_local.day}일 {value_local:%H:%M} ({value_local:%Z})"

    @staticmethod
    def fetch_timeline() -> CodexResetTimelineResponse:
        response = requests.get(
            config.CODEX_RESET_TIMELINE_URL,
            timeout=10,
        )
        response.raise_for_status()

        timeline = CodexResetTimelineResponse.model_validate_json(response.text)

        return timeline

    @staticmethod
    def find_latest_banked_announcement(
        timeline: CodexResetTimelineResponse,
    ) -> CodexResetTimelineEvent | None:
        return max(
            (event for event in timeline.events if event.banked_state == "announced"),
            key=lambda event: event.announced_at,
            default=None,
        )

    @staticmethod
    def build_banked_announcement_message(
        announcement: CodexResetTimelineEvent | None,
    ) -> str:
        if announcement is None:
            return strings.codex_banked_announcement_unavailable_msg

        announced_at = CodexResetService._format_datetime(
            announcement.announced_at,
        )

        return strings.codex_banked_announcement_msg.format(
            announced_at=announced_at,
            source_url=announcement.url,
        )
