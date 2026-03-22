import time
from unittest.mock import MagicMock, patch

import pytest

from modules.admin import AdminManager
from modules.database import PendingAction
from resources import strings


@pytest.fixture
def admin():
    bot = MagicMock()
    gemini_chat = MagicMock()
    return AdminManager(bot, gemini_chat)


def make_message(text, chat_id=1, user_id=1):
    msg = MagicMock()
    msg.text = text
    msg.chat.id = chat_id
    msg.from_user.id = user_id
    return msg


class TestAllowChatHandler:
    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_admin_allow_shows_confirmation(self, admin):
        msg = make_message("/allow_chat", chat_id=42, user_id=100)
        msg.chat.title = "테스트 채널"
        msg.chat.first_name = None
        admin.bot.reply_to.return_value.message_id = 999
        admin.bot.reply_to.return_value.chat.id = 42
        admin.allow_chat_handler(msg)
        admin.gemini_chat.allow_chat.assert_not_called()
        row = PendingAction.get_or_none(PendingAction.msg_id == 999)
        assert row is not None
        assert row.action == "allow"
        assert row.chat_id == 42

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, admin):
        msg = make_message("/allow_chat", user_id=999)
        admin.allow_chat_handler(msg)
        admin.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_invalid_argument(self, admin):
        msg = make_message("/allow_chat abc", user_id=100)
        admin.allow_chat_handler(msg)
        admin.bot.reply_to.assert_called_once_with(msg, strings.admin_allow_usage_msg)


class TestDenyChatHandler:
    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_admin_deny_shows_confirmation(self, admin):
        admin.gemini_chat.is_chat_allowed.return_value = True
        admin.gemini_chat.get_chat_name.return_value = "테스트"
        msg = make_message("/deny_chat 42", user_id=100)
        admin.bot.reply_to.return_value.message_id = 888
        admin.bot.reply_to.return_value.chat.id = 1
        admin.deny_chat_handler(msg)
        admin.gemini_chat.deny_chat.assert_not_called()
        row = PendingAction.get_or_none(PendingAction.msg_id == 888)
        assert row is not None
        assert row.action == "deny"

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_deny_not_in_list(self, admin):
        admin.gemini_chat.is_chat_allowed.return_value = False
        msg = make_message("/deny_chat 42", user_id=100)
        admin.deny_chat_handler(msg)
        admin.bot.reply_to.assert_called_once_with(msg, strings.admin_deny_chat_not_found_msg.format(chat_id=42))

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, admin):
        msg = make_message("/deny_chat 42", user_id=999)
        admin.deny_chat_handler(msg)
        admin.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)


class TestAdminCallback:
    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_allow_confirm(self, admin):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 100
        call.data = "allow_confirm:999"
        admin.handle_admin_callback(call)
        admin.gemini_chat.allow_chat.assert_called_once_with(42, "테스트")
        admin.bot.edit_message_text.assert_called_once()
        assert PendingAction.get_or_none(PendingAction.msg_id == 999) is None

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_deny_confirm(self, admin):
        PendingAction.create(msg_id=888, action="deny", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 100
        call.data = "deny_confirm:888"
        admin.handle_admin_callback(call)
        admin.gemini_chat.deny_chat.assert_called_once_with(42)
        admin.bot.edit_message_text.assert_called_once()

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_cancel(self, admin):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 100
        call.data = "allow_cancel:999"
        admin.handle_admin_callback(call)
        admin.gemini_chat.allow_chat.assert_not_called()
        admin.bot.edit_message_text.assert_called_once()
        assert PendingAction.get_or_none(PendingAction.msg_id == 999) is None

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_non_admin_ignored(self, admin):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 999
        call.data = "allow_confirm:999"
        admin.handle_admin_callback(call)
        admin.gemini_chat.allow_chat.assert_not_called()
        assert PendingAction.get_or_none(PendingAction.msg_id == 999) is not None

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_set_model_callback(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_model:gemini-2.5-pro"
        admin.handle_admin_callback(call)
        admin.gemini_chat.set_model.assert_called_once_with("gemini-2.5-pro")
        admin.bot.edit_message_text.assert_called_once()

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_set_model_cancel_callback(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_model_cancel:0"
        admin.handle_admin_callback(call)
        admin.gemini_chat.set_model.assert_not_called()
        admin.bot.edit_message_text.assert_called_once_with(
            strings.admin_cancel_msg,
            call.message.chat.id,
            call.message.message_id,
        )


class TestPendingExpiry:
    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_expired_entries_cleaned(self, admin):
        PendingAction.create(msg_id=1, action="allow", chat_id=10, name="old", timestamp=time.time() - 301)
        PendingAction.create(msg_id=2, action="deny", chat_id=20, name="fresh", timestamp=time.time())
        admin._cleanup_expired_pending()
        assert PendingAction.get_or_none(PendingAction.msg_id == 1) is None
        assert PendingAction.get_or_none(PendingAction.msg_id == 2) is not None

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_all_expired(self, admin):
        PendingAction.create(msg_id=1, action="allow", chat_id=10, name="a", timestamp=time.time() - 400)
        PendingAction.create(msg_id=2, action="deny", chat_id=20, name="b", timestamp=time.time() - 500)
        admin._cleanup_expired_pending()
        assert PendingAction.select().count() == 0

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_expired_callback_ignored(self, admin):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="expired", timestamp=time.time() - 301)
        call = MagicMock()
        call.from_user.id = 100
        call.data = "allow_confirm:999"
        admin.handle_admin_callback(call)
        admin.gemini_chat.allow_chat.assert_not_called()


class TestCallbackPrefixes:
    def test_all_handled_actions_registered(self):
        expected = {
            "allow_confirm",
            "allow_cancel",
            "deny_confirm",
            "deny_cancel",
            "ask_settings",
            "ask_settings_cancel",
            "set_model",
            "set_model_cancel",
            "set_search",
            "set_search_cancel",
            "set_prompt",
            "set_prompt_cancel",
        }
        assert AdminManager.CALLBACK_PREFIXES == expected


class TestAskSettingsHandler:
    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_shows_menu(self, admin):
        admin.gemini_chat.model = "gemini-2.5-flash"
        admin.gemini_chat.search_grounding = False
        admin.gemini_chat.custom_prompt = ""
        msg = make_message("/ask_settings", user_id=100)
        admin.ask_settings_handler(msg)
        admin.bot.reply_to.assert_called_once()
        call_args = admin.bot.reply_to.call_args
        assert "gemini-2.5-flash" in call_args[0][1]
        assert "reply_markup" in call_args.kwargs

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, admin):
        msg = make_message("/ask_settings", user_id=999)
        admin.ask_settings_handler(msg)
        admin.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_model_callback(self, admin):
        admin.gemini_chat.model = "gemini-2.5-flash"
        admin.gemini_chat.list_models.return_value = ["gemini-2.5-flash", "gemini-2.5-pro"]
        call = MagicMock()
        call.from_user.id = 100
        call.data = "ask_settings:model"
        admin.handle_admin_callback(call)
        admin.bot.edit_message_text.assert_called_once()
        call_args = admin.bot.edit_message_text.call_args
        assert "gemini-2.5-flash" in call_args[0][0]
        assert "reply_markup" in call_args.kwargs

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_search_callback(self, admin):
        admin.gemini_chat.search_grounding = False
        call = MagicMock()
        call.from_user.id = 100
        call.data = "ask_settings:search"
        admin.handle_admin_callback(call)
        admin.bot.edit_message_text.assert_called_once()
        call_args = admin.bot.edit_message_text.call_args
        assert "reply_markup" in call_args.kwargs

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_set_search_true(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_search:true"
        admin.handle_admin_callback(call)
        admin.gemini_chat.set_search_grounding.assert_called_once_with(True)
        admin.bot.edit_message_text.assert_called_once()

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_set_search_false(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_search:false"
        admin.handle_admin_callback(call)
        admin.gemini_chat.set_search_grounding.assert_called_once_with(False)

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_allowlist_callback(self, admin):
        admin.gemini_chat.list_allowed_chats.return_value = [{"id": 1, "name": "A"}]
        call = MagicMock()
        call.from_user.id = 100
        call.data = "ask_settings:allowlist"
        admin.handle_admin_callback(call)
        admin.bot.edit_message_text.assert_called_once()

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_prompt_callback(self, admin):
        admin.gemini_chat.custom_prompt = "Be formal."
        call = MagicMock()
        call.from_user.id = 100
        call.data = "ask_settings:prompt"
        admin.handle_admin_callback(call)
        admin.bot.edit_message_text.assert_called_once()
        call_args = admin.bot.edit_message_text.call_args
        assert "Be formal." in call_args[0][0]
        assert "reply_markup" in call_args.kwargs

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_set_prompt_clear(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_prompt:clear"
        admin.handle_admin_callback(call)
        admin.gemini_chat.set_custom_prompt.assert_called_once_with("")

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_set_prompt_edit_sends_force_reply(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_prompt:edit"
        admin.handle_admin_callback(call)
        admin.bot.send_message.assert_called_once()
        call_kwargs = admin.bot.send_message.call_args
        assert "reply_markup" in call_kwargs.kwargs

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_handle_prompt_reply(self, admin):
        admin._pending_prompt = (100, 1, time.time())
        msg = make_message("Always be polite.", chat_id=1, user_id=100)
        admin.handle_prompt_reply(msg)
        admin.gemini_chat.set_custom_prompt.assert_called_once_with("Always be polite.")
        admin.bot.reply_to.assert_called_once_with(msg, strings.set_prompt_done_msg)
        assert admin._pending_prompt is None

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_handle_prompt_reply_wrong_user(self, admin):
        admin._pending_prompt = (100, 1, time.time())
        msg = make_message("hack prompt", chat_id=1, user_id=999)
        admin.handle_prompt_reply(msg)
        admin.gemini_chat.set_custom_prompt.assert_not_called()

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_handle_prompt_reply_wrong_chat(self, admin):
        admin._pending_prompt = (100, 1, time.time())
        msg = make_message("prompt text", chat_id=999, user_id=100)
        admin.handle_prompt_reply(msg)
        admin.gemini_chat.set_custom_prompt.assert_not_called()

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_handle_prompt_reply_expired(self, admin):
        admin._pending_prompt = (100, 1, time.time() - 301)
        msg = make_message("late reply", chat_id=1, user_id=100)
        admin.handle_prompt_reply(msg)
        admin.gemini_chat.set_custom_prompt.assert_not_called()
        assert admin._pending_prompt is None

    @patch("modules.admin.config.ADMIN_USER_ID", 100)
    def test_cancel_callback(self, admin):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "ask_settings_cancel:0"
        admin.handle_admin_callback(call)
        admin.bot.edit_message_text.assert_called_once_with(
            strings.admin_cancel_msg,
            call.message.chat.id,
            call.message.message_id,
        )
