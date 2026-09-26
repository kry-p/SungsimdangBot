import re
from datetime import datetime, timezone
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests

from config import config
from modules.api_models import CodexResetForecastResponse, CodexResetHistoryEvent, CodexResetHistoryResponse
from resources import strings

EVIDENCE_PATH_PATTERN = re.compile(r"/evidence/[A-Za-z0-9-]+/")
CODEX_RESET_TIMEZONE = ZoneInfo("Asia/Seoul")


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

        value_local = value.astimezone(CODEX_RESET_TIMEZONE)
        return strings.codex_reset_datetime_msg.format(
            year=value_local.year,
            month=value_local.month,
            day=value_local.day,
            time=value_local.strftime("%H:%M"),
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
            and event.scope == "all"
            and event.event_kind in {"intent", "scheduled"}
            and event.status == "active"
            and (last_reset_at is None or event.announced_at > last_reset_at)
        )
        return max(notices, key=lambda event: event.announced_at, default=None)

    @staticmethod
    def build_active_notice_message(notice: CodexResetHistoryEvent | None) -> str:
        if notice is None:
            return ""
        message = strings.codex_reset_active_notice_msg.format(
            announced_at=CodexResetService._format_datetime(notice.announced_at),
        )
        # targetAt can mark the end of a promised day rather than an exact reset time.
        if notice.evidence_url and EVIDENCE_PATH_PATTERN.fullmatch(notice.evidence_url):
            message += strings.codex_reset_notice_source_msg.format(
                url=urljoin(config.CODEX_RESET_HISTORY_URL, notice.evidence_url),
            )
        return message + "\n\n"

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
