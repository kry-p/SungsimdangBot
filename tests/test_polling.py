import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import telebot
from telebot import apihelper

from modules import polling

POLLING_TEST_TIMEOUT = 5
POLLING_STOP_TIMEOUT = 1


def _run_threaded_polling(bot, monkeypatch, get_updates):
    logger = MagicMock()
    polling_errors = []
    monkeypatch.setattr(bot, "get_me", lambda: SimpleNamespace(username="test"))
    monkeypatch.setattr(bot, "get_updates", get_updates)
    monkeypatch.setattr(telebot.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(polling, "BOT_POLLING_INTERVAL", 0)

    def run():
        try:
            polling.run_polling(bot, logger)
        except BaseException as error:
            polling_errors.append(error)

    polling_thread = threading.Thread(target=run, daemon=True)
    polling_thread.start()

    try:
        polling_thread.join(timeout=POLLING_TEST_TIMEOUT)
        if polling_thread.is_alive():
            bot.stop_polling()
            polling_thread.join(timeout=POLLING_STOP_TIMEOUT)
            raise AssertionError("Polling did not finish within the test timeout")
        if polling_errors:
            raise polling_errors[0]
    finally:
        bot.stop_bot()


def test_create_bot_configures_skip_pending(monkeypatch):
    expected_bot = MagicMock()
    telebot_class = MagicMock(return_value=expected_bot)
    monkeypatch.setattr(polling.telebot, "TeleBot", telebot_class)

    result = polling.create_bot("1:test")

    assert result is expected_bot
    telebot_class.assert_called_once_with("1:test", parse_mode=None, skip_pending=True)


def test_run_polling_uses_project_configuration():
    bot = MagicMock()
    logger = MagicMock()

    polling.run_polling(bot, logger)

    logger.add_file_handler_to.assert_called_once_with(telebot.logger)
    assert logger.log_info.call_args_list == [
        call("Starts polling"),
        call("Bot instance is running"),
        call("Polling stopped"),
    ]
    bot.infinity_polling.assert_called_once_with(
        interval=polling.BOT_POLLING_INTERVAL,
        timeout=polling.BOT_REQUEST_TIMEOUT,
        long_polling_timeout=polling.BOT_LONG_POLLING_TIMEOUT,
    )


def test_threaded_polling_recovers_after_initial_skip_failure(monkeypatch):
    bot = polling.create_bot("1:test")
    get_updates_call_count = 0

    def flaky_get_updates(*_args, **_kwargs):
        nonlocal get_updates_call_count
        get_updates_call_count += 1
        if get_updates_call_count == 1:
            raise RuntimeError("temporary skip failure")
        if get_updates_call_count >= 3:
            bot.stop_polling()
        return []

    _run_threaded_polling(bot, monkeypatch, flaky_get_updates)

    assert get_updates_call_count > 1


def test_threaded_polling_recovers_after_runtime_failure(monkeypatch):
    bot = polling.create_bot("1:test")
    successful_poll_count = 0
    failure_observed = False
    recovered = False

    def record_processed_updates(_updates):
        nonlocal successful_poll_count
        successful_poll_count += 1

    def flaky_get_updates(*_args, **_kwargs):
        nonlocal failure_observed, recovered
        if successful_poll_count and not failure_observed:
            failure_observed = True
            raise RuntimeError("temporary polling failure")
        if failure_observed:
            recovered = True
            bot.stop_polling()
        return []

    monkeypatch.setattr(bot, "process_new_updates", record_processed_updates)
    _run_threaded_polling(bot, monkeypatch, flaky_get_updates)

    assert failure_observed
    assert recovered
    assert successful_poll_count >= 2


def test_threaded_polling_recovers_after_api_exception(monkeypatch):
    bot = polling.create_bot("1:test")
    successful_poll_count = 0
    failure_observed = False
    recovered = False

    def record_processed_updates(_updates):
        nonlocal successful_poll_count
        successful_poll_count += 1

    def flaky_get_updates(*_args, **_kwargs):
        nonlocal failure_observed, recovered
        if successful_poll_count and not failure_observed:
            failure_observed = True
            raise apihelper.ApiException("temporary API failure", "getUpdates", None)
        if failure_observed:
            recovered = True
            bot.stop_polling()
        return []

    monkeypatch.setattr(bot, "process_new_updates", record_processed_updates)
    _run_threaded_polling(bot, monkeypatch, flaky_get_updates)

    assert failure_observed
    assert recovered
    assert successful_poll_count >= 2


def test_threaded_polling_recovers_after_consecutive_failures(monkeypatch):
    bot = polling.create_bot("1:test")
    successful_poll_count = 0
    failure_count = 0
    recovered = False

    def record_processed_updates(_updates):
        nonlocal successful_poll_count
        successful_poll_count += 1

    def flaky_get_updates(*_args, **_kwargs):
        nonlocal failure_count, recovered
        if successful_poll_count and failure_count < 3:
            failure_count += 1
            raise RuntimeError("repeated polling failure")
        if failure_count == 3:
            recovered = True
            bot.stop_polling()
        return []

    monkeypatch.setattr(bot, "process_new_updates", record_processed_updates)
    _run_threaded_polling(bot, monkeypatch, flaky_get_updates)

    assert failure_count == 3
    assert recovered
    assert successful_poll_count >= 2
