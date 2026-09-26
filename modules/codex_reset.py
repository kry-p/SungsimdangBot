from datetime import datetime, timezone

import requests

from config import config
from modules.api_models import CodexResetForecastResponse, CodexResetHistoryEvent, CodexResetHistoryResponse
from resources import strings


class CodexResetService:
    @staticmethod
    def fetch_forecast() -> CodexResetForecastResponse:
        response = requests.get(config.CODEX_RESET_FORECAST_URL, timeout=10)
        response.raise_for_status()
        return CodexResetForecastResponse.model_validate_json(response.text)

    @staticmethod
    def build_forecast_message(
        forecast: CodexResetForecastResponse,
        now: datetime | None = None,
    ) -> str:
        now = now or datetime.now(timezone.utc)
        probability = strings.codex_reset_probability_unavailable_msg
        if (
            forecast.probabilities is not None
            and forecast.display_mode == "probability"
            and forecast.publication_state not in {"stale", "unavailable"}
            and forecast.valid_until is not None
            and forecast.valid_until > now
        ):
            probability = f"{forecast.probabilities.h24.display}%"

        last_reset_at = forecast.latest_reset.occurred_at if forecast.latest_reset else None
        return strings.codex_reset_forecast_msg.format(
            last_reset_at=CodexResetService._format_datetime(last_reset_at),
            probability_24h=probability,
        )

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        if value is None:
            return strings.codex_reset_date_unavailable_msg

        value_local = value.astimezone(config.TIMEZONE)
        return strings.codex_reset_datetime_msg.format(
            year=value_local.year,
            month=value_local.month,
            day=value_local.day,
            time=value_local.strftime("%H:%M"),
            timezone=value_local.strftime("%Z"),
        )

    @staticmethod
    def fetch_history() -> CodexResetHistoryResponse:
        response = requests.get(config.CODEX_RESET_HISTORY_URL, timeout=10)
        response.raise_for_status()
        return CodexResetHistoryResponse.model_validate_json(response.text)

    @staticmethod
    def find_latest_active_notice(
        history: CodexResetHistoryResponse,
        last_reset_at: datetime | None,
    ) -> CodexResetHistoryEvent | None:
        notices = (
            event
            for event in history.items
            if event.kind == "special_global"
            and event.event_kind in {"intent", "scheduled"}
            and event.status == "active"
            and (last_reset_at is None or event.announced_at > last_reset_at)
        )
        return max(notices, key=lambda event: event.announced_at, default=None)

    @staticmethod
    def build_active_notice_message(notice: CodexResetHistoryEvent | None) -> str:
        if notice is None:
            return ""
        return strings.codex_reset_active_notice_msg.format(
            announced_at=CodexResetService._format_datetime(notice.announced_at),
        )

    @staticmethod
    def find_latest_banked_update(history: CodexResetHistoryResponse) -> CodexResetHistoryEvent | None:
        banked_events = (event for event in history.items if event.kind == "banked" and event.status != "superseded")
        return max(banked_events, key=lambda event: event.announced_at, default=None)

    @staticmethod
    def build_banked_updates_message(update: CodexResetHistoryEvent | None) -> str:
        message = strings.codex_banked_updates_header_msg
        if update is None:
            return message + strings.codex_banked_updates_unavailable_msg
        return message + strings.codex_banked_update_msg.format(
            updated_at=CodexResetService._format_datetime(update.announced_at),
        )
