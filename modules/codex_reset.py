from datetime import datetime

import requests

from config import config
from modules.api_models import CodexResetForecastResponse, CodexResetTimelineEvent, CodexResetTimelineResponse
from resources import strings

BANKED_RESET_STATES = (
    "announced",
    "arriving",
    "available",
)


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
        confidence = strings.codex_reset_confidence_labels.get(
            forecast.confidence,
            strings.codex_reset_confidence_labels["unknown"],
        )
        last_reset_at = CodexResetService._format_datetime(
            forecast.last_reset_at,
        )

        return strings.codex_reset_forecast_msg.format(
            last_reset_at=last_reset_at,
            probability_24h=forecast.probabilities.rounded_24h,
            confidence=confidence,
        )

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        if value is None:
            return strings.codex_reset_date_unavailable_msg

        value_local = value.astimezone(config.TIMEZONE)

        formatted_datetime = strings.codex_reset_datetime_msg.format(
            year=value_local.year,
            month=value_local.month,
            day=value_local.day,
            time=value_local.strftime("%H:%M"),
            timezone=value_local.strftime("%Z"),
        )

        return formatted_datetime

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
    def find_latest_banked_updates(
        timeline: CodexResetTimelineResponse,
    ) -> dict[str, CodexResetTimelineEvent]:
        latest_updates = {}

        for event in timeline.events:
            state = event.banked_state
            if state not in BANKED_RESET_STATES:
                continue

            latest_event = latest_updates.get(state)
            if latest_event is None or event.announced_at > latest_event.announced_at:
                latest_updates[state] = event

        visible_updates = {}
        latest_timestamp = None

        for state in BANKED_RESET_STATES:
            event = latest_updates.get(state)
            if event is None:
                continue

            if latest_timestamp is not None and event.announced_at < latest_timestamp:
                continue

            visible_updates[state] = event
            latest_timestamp = event.announced_at

        return visible_updates

    @staticmethod
    def build_banked_updates_message(
        updates: dict[str, CodexResetTimelineEvent],
    ) -> str:
        message = strings.codex_banked_updates_header_msg

        if not updates:
            return message + strings.codex_banked_updates_unavailable_msg

        update_messages = []

        for state in BANKED_RESET_STATES:
            event = updates.get(state)
            if event is None:
                continue

            update_messages.append(
                strings.codex_banked_update_msg.format(
                    label=strings.codex_banked_state_labels[state],
                    updated_at=CodexResetService._format_datetime(event.announced_at),
                )
            )

        return message + "\n".join(update_messages)
