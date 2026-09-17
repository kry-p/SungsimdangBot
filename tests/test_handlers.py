from unittest.mock import MagicMock

from bin.handlers import register_commands, register_handlers
from resources import strings
from tests.conftest import make_message


def _capture_handlers(hub, logger):
    """register_handlers를 호출하고 등록된 핸들러를 캡처한다."""
    bot = MagicMock()
    captured = {}

    def capture_message_handler(**kwargs):
        def decorator(func):
            commands = kwargs.get("commands")
            content_types = kwargs.get("content_types")
            has_func_filter = kwargs.get("func") is not None

            if commands:
                for cmd in commands:
                    captured[cmd] = func
            elif content_types and "photo" in content_types:
                captured["photo"] = func
            elif content_types and "location" in content_types:
                captured["location"] = func
            elif content_types and "text" in content_types:
                captured["text"] = func
            elif has_func_filter and not commands and not content_types:
                captured["prompt_reply"] = func
            return func

        return decorator

    def capture_callback_handler(**kwargs):
        def decorator(func):
            captured["callback"] = func
            return func

        return decorator

    bot.message_handler = capture_message_handler
    bot.callback_query_handler = capture_callback_handler
    register_handlers(bot, hub, logger)
    return bot, captured


def test_register_commands_uses_descriptions_from_strings():
    bot = MagicMock()
    register_commands(bot)
    commands = bot.set_my_commands.call_args.args[0]
    actual = [(command.command, command.description) for command in commands]
    assert actual == list(strings.bot_command_descriptions.items())


def test_register_commands_includes_codex():
    bot = MagicMock()

    register_commands(bot)

    commands = bot.set_my_commands.call_args.args[0]
    actual = [(command.command, command.description) for command in commands]
    assert ("codex", "Codex 초기화 정보") in actual


class TestSafeHandlerErrorBoundary:
    def test_exception_logs_and_replies_error(self):
        hub = MagicMock()
        hub.search_handler.side_effect = Exception("API error")
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)

        msg = make_message("/search test")
        handlers["search"](msg)

        logger.log_error.assert_called_once()
        bot.reply_to.assert_called_once_with(msg, strings.generic_error_msg)

    def test_exception_in_reply_does_not_propagate(self):
        hub = MagicMock()
        hub.ask_handler.side_effect = Exception("Gemini error")
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)
        bot.reply_to.side_effect = Exception("Telegram API down")

        msg = make_message("/ask test")
        handlers["ask"](msg)

        assert logger.log_error.call_count == 2
        assert bot.reply_to.call_count == 3

    def test_safe_handler_not_applied_to_ping(self):
        hub = MagicMock()
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)

        msg = make_message("/ping")
        handlers["ping"](msg)

        bot.send_message.assert_called_once_with(msg.chat.id, strings.working_msg)
        logger.log_error.assert_not_called()

    def test_codex_handler_exception_is_caught(self):
        hub = MagicMock()
        hub.codex_handler.side_effect = Exception("unexpected error")
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)

        msg = make_message("/codex")
        handlers["codex"](msg)

        logger.log_error.assert_called_once()
        bot.reply_to.assert_called_once_with(msg, strings.generic_error_msg)


class TestHandlerDelegation:
    def test_codex_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/codex")
        handlers["codex"](msg)

        hub.codex_handler.assert_called_once_with(msg)

    def test_commute_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/commute")
        handlers["commute"](msg)

        hub.commute_handler.assert_called_once_with(msg)

    def test_search_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/search test")
        handlers["search"](msg)
        hub.search_handler.assert_called_once_with(msg)

    def test_ask_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/ask question")
        handlers["ask"](msg)
        hub.ask_handler.assert_called_once_with(msg)

    def test_dday_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/dday 2025 12 25")
        handlers["dday"](msg)
        hub.d_day.assert_called_once_with(msg)

    def test_location_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = MagicMock()
        msg.location.latitude = 37.5
        msg.location.longitude = 127.0
        handlers["location"](msg)
        hub.geolocation_info.assert_called_once_with(msg, 37.5, 127.0)

    def test_namu_delegates_to_hub(self):
        hub = MagicMock()
        hub.web_manager.namuwiki_search.return_value = "result"
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)

        msg = make_message("/namu test")
        handlers["namu"](msg)
        hub.web_manager.namuwiki_search.assert_called_once_with(msg)

    def test_clear_chat_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/clear_chat")
        handlers["clear_chat"](msg)
        hub.clear_chat_handler.assert_called_once_with(msg)

    def test_text_handler_ignores_commands(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/unknown_command")
        handlers["text"](msg)
        hub.ordinary_message.assert_not_called()

    def test_text_handler_delegates_ordinary_message(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("hello")
        handlers["text"](msg)
        hub.ordinary_message.assert_called_once_with(msg)

    def test_laftel_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/laftel")
        handlers["laftel"](msg)
        hub.laftel.show_portal.assert_called_once_with(msg.chat.id)

    def test_spotify_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        msg = make_message("/spotify 아이유")
        handlers["spotify"](msg)
        hub.spotify_search_handler.assert_called_once_with(msg)

    def test_spotify_callback_delegates_to_hub(self):
        hub = MagicMock()
        logger = MagicMock()
        _, handlers = _capture_handlers(hub, logger)

        query = MagicMock()
        query.data = "spotify_track:" + "A" * 22
        handlers["callback"](query)

        hub.handle_spotify_callback.assert_called_once_with(query)

    def test_stale_commute_callback_is_ignored(self):
        hub = MagicMock()
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)

        query = MagicMock()
        query.data = "commute:set:123"
        handlers["callback"](query)

        hub.handle_commute_callback.assert_not_called()
        bot.send_message.assert_not_called()


class TestCallbackErrorBoundary:
    def test_callback_exception_is_logged(self):
        hub = MagicMock()
        hub.handle_admin_callback.side_effect = Exception("db error")
        logger = MagicMock()
        bot, handlers = _capture_handlers(hub, logger)

        query = MagicMock()
        query.data = "allow_confirm:123"
        handlers["callback"](query)

        logger.log_error.assert_called_once()
