import time

import telebot

from config import config
from modules.database import PendingAction
from resources import strings

CANCEL_ACTIONS = frozenset(
    {
        "ask_settings_cancel",
        "set_model_cancel",
        "set_search_cancel",
        "set_prompt_cancel",
    }
)


class AdminManager:
    CALLBACK_PREFIXES = frozenset(
        {
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
    )

    PROMPT_INPUT_TIMEOUT = 300
    PENDING_TIMEOUT = 300

    @staticmethod
    def is_admin_callback(data):
        return bool(data and ":" in data and data.split(":")[0] in AdminManager.CALLBACK_PREFIXES)

    @staticmethod
    def is_admin(user_id):
        return user_id == config.ADMIN_USER_ID

    def __init__(self, bot, gemini_chat):
        self.bot = bot
        self.gemini_chat = gemini_chat
        self._pending_prompt = None

    # --- Callback dispatch ---

    _SETTINGS_HANDLERS = {
        "ask_settings": "_handle_ask_settings_callback",
        "set_model": "_handle_set_model",
        "set_search": "_handle_set_search",
        "set_prompt": "_handle_set_prompt",
    }

    def handle_admin_callback(self, call):
        if not self.is_admin(call.from_user.id):
            return
        self._cleanup_expired_pending()
        action, value = call.data.split(":", 1)

        handler_name = self._SETTINGS_HANDLERS.get(action)
        if handler_name:
            getattr(self, handler_name)(call, value)
            return

        if action in CANCEL_ACTIONS:
            self.bot.edit_message_text(
                strings.admin_cancel_msg,
                call.message.chat.id,
                call.message.message_id,
            )
            return

        self._handle_pending_action(call, action, int(value))

    def _handle_set_model(self, call, value):
        self.gemini_chat.set_model(value)
        self.bot.edit_message_text(
            strings.set_model_done_msg.format(model=value),
            call.message.chat.id,
            call.message.message_id,
        )

    def _handle_set_search(self, call, value):
        enabled = value == "true"
        self.gemini_chat.set_search_grounding(enabled)
        msg = strings.set_search_enabled_msg if enabled else strings.set_search_disabled_msg
        self.bot.edit_message_text(msg, call.message.chat.id, call.message.message_id)

    def _handle_set_prompt(self, call, value):
        if value == "edit":
            self._pending_prompt = (call.from_user.id, call.message.chat.id, time.time())
            self.bot.edit_message_text(strings.set_prompt_input_msg, call.message.chat.id, call.message.message_id)
            self.bot.send_message(
                call.message.chat.id,
                strings.set_prompt_input_msg,
                reply_markup=telebot.types.ForceReply(selective=True),
            )
        elif value == "clear":
            self.gemini_chat.set_custom_prompt("")
            self.bot.edit_message_text(strings.set_prompt_cleared_msg, call.message.chat.id, call.message.message_id)

    def _handle_pending_action(self, call, action, msg_id):
        pending = PendingAction.get_or_none(PendingAction.msg_id == msg_id)
        if not pending:
            return
        chat_id = pending.chat_id
        name = pending.name
        pending.delete_instance()
        if action == "allow_confirm":
            self.gemini_chat.allow_chat(chat_id, name)
            self.bot.edit_message_text(
                strings.admin_allow_chat_msg.format(name=name or chat_id, chat_id=chat_id),
                call.message.chat.id,
                call.message.message_id,
            )
        elif action == "deny_confirm":
            self.gemini_chat.deny_chat(chat_id)
            self.bot.edit_message_text(
                strings.admin_deny_chat_msg.format(name=name or chat_id, chat_id=chat_id),
                call.message.chat.id,
                call.message.message_id,
            )
        elif action in ("allow_cancel", "deny_cancel"):
            self.bot.edit_message_text(
                strings.admin_cancel_msg,
                call.message.chat.id,
                call.message.message_id,
            )

    # --- Allow / Deny chat ---

    def allow_chat_handler(self, message):
        if not self.is_admin(message.from_user.id):
            self.bot.reply_to(message, strings.admin_only_msg)
            return
        parts = message.text.split()
        if len(parts) < 2:
            chat_id = message.chat.id
            name = getattr(message.chat, "title", None) or getattr(message.chat, "first_name", "") or ""
        else:
            try:
                chat_id = int(parts[1])
            except ValueError:
                self.bot.reply_to(message, strings.admin_allow_usage_msg)
                return
            try:
                chat_info = self.bot.get_chat(chat_id)
                name = getattr(chat_info, "title", None) or getattr(chat_info, "first_name", "") or ""
            except Exception:
                name = ""
        confirm_text = strings.admin_allow_confirm_msg.format(name=name or chat_id, chat_id=chat_id)
        self._send_pending_confirmation(message, "allow", chat_id, name, confirm_text)

    def deny_chat_handler(self, message):
        if not self.is_admin(message.from_user.id):
            self.bot.reply_to(message, strings.admin_only_msg)
            return
        parts = message.text.split()
        if len(parts) < 2:
            chat_id = message.chat.id
        else:
            try:
                chat_id = int(parts[1])
            except ValueError:
                self.bot.reply_to(message, strings.admin_deny_usage_msg)
                return
        if not self.gemini_chat.is_chat_allowed(chat_id):
            self.bot.reply_to(message, strings.admin_deny_chat_not_found_msg.format(chat_id=chat_id))
            return
        name = self.gemini_chat.get_chat_name(chat_id)
        confirm_text = strings.admin_deny_confirm_msg.format(name=name or chat_id, chat_id=chat_id)
        self._send_pending_confirmation(message, "deny", chat_id, name, confirm_text)

    def _send_pending_confirmation(self, message, action, chat_id, name, confirm_text):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_confirm_btn, callback_data=f"{action}_confirm:0"),
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data=f"{action}_cancel:0"),
        )
        sent = self.bot.reply_to(message, confirm_text, reply_markup=keyboard)
        msg_id = sent.message_id
        PendingAction.create(msg_id=msg_id, action=action, chat_id=chat_id, name=name, timestamp=time.time())
        self.bot.edit_message_reply_markup(
            sent.chat.id,
            msg_id,
            reply_markup=self._build_admin_keyboard(f"{action}_confirm:{msg_id}", f"{action}_cancel:{msg_id}"),
        )

    # --- Ask settings menu ---

    def ask_settings_handler(self, message):
        if not self.is_admin(message.from_user.id):
            self.bot.reply_to(message, strings.admin_only_msg)
            return
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.ask_settings_model_btn, callback_data="ask_settings:model"),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.ask_settings_search_btn, callback_data="ask_settings:search"),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.ask_settings_prompt_btn, callback_data="ask_settings:prompt"),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                strings.ask_settings_allowlist_btn, callback_data="ask_settings:allowlist"
            ),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data="ask_settings_cancel:0"),
        )
        status = self._build_ask_settings_status()
        self.bot.reply_to(message, status, reply_markup=keyboard)

    def _build_ask_settings_status(self):
        model = self.gemini_chat.model
        search = strings.status_enabled if self.gemini_chat.search_grounding else strings.status_disabled
        prompt = self.gemini_chat.custom_prompt or strings.status_empty
        if len(prompt) > 50:
            prompt = prompt[:50] + "..."
        return strings.ask_settings_msg.format(model=model, search=search, prompt=prompt)

    def _handle_ask_settings_callback(self, call, value):
        handler = {
            "model": self._show_model_selection,
            "search": self._show_search_toggle,
            "allowlist": self._show_allowlist,
            "prompt": self._show_prompt_settings,
        }.get(value)
        if handler:
            handler(call.message.chat.id, call.message.message_id)

    def _show_model_selection(self, chat_id, msg_id):
        models = self.gemini_chat.list_models()
        if not models:
            self.bot.edit_message_text(strings.set_model_error_msg, chat_id, msg_id)
            return
        keyboard = telebot.types.InlineKeyboardMarkup()
        for model_name in models:
            callback_data = f"set_model:{model_name}"
            if len(callback_data.encode()) > 64:
                continue
            keyboard.row(telebot.types.InlineKeyboardButton(model_name, callback_data=callback_data))
        if not keyboard.keyboard:
            self.bot.edit_message_text(strings.set_model_error_msg, chat_id, msg_id)
            return
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data="set_model_cancel:0"),
        )
        self.bot.edit_message_text(
            strings.set_model_msg.format(model=self.gemini_chat.model), chat_id, msg_id, reply_markup=keyboard
        )

    def _show_search_toggle(self, chat_id, msg_id):
        status = strings.status_enabled if self.gemini_chat.search_grounding else strings.status_disabled
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_enable_btn, callback_data="set_search:true"),
            telebot.types.InlineKeyboardButton(strings.admin_disable_btn, callback_data="set_search:false"),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data="set_search_cancel:0"),
        )
        self.bot.edit_message_text(strings.set_search_msg.format(status=status), chat_id, msg_id, reply_markup=keyboard)

    def _show_allowlist(self, chat_id, msg_id):
        chats = self.gemini_chat.list_allowed_chats()
        if not chats:
            self.bot.edit_message_text(strings.admin_list_chats_empty_msg, chat_id, msg_id)
        else:
            chat_list = "\n".join(f"{c['id']} ({c['name']})" if c["name"] else str(c["id"]) for c in chats)
            self.bot.edit_message_text(strings.admin_list_chats_msg.format(chat_list), chat_id, msg_id)

    def _show_prompt_settings(self, chat_id, msg_id):
        current = self.gemini_chat.custom_prompt or strings.status_empty
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.ask_settings_prompt_edit_btn, callback_data="set_prompt:edit"),
            telebot.types.InlineKeyboardButton(strings.ask_settings_prompt_clear_btn, callback_data="set_prompt:clear"),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data="set_prompt_cancel:0"),
        )
        self.bot.edit_message_text(
            strings.set_prompt_msg.format(prompt=current), chat_id, msg_id, reply_markup=keyboard
        )

    # --- ForceReply handler ---

    def handle_prompt_reply(self, message):
        if not self._pending_prompt:
            return
        user_id, chat_id, timestamp = self._pending_prompt
        if message.from_user.id != user_id or message.chat.id != chat_id:
            return
        if time.time() - timestamp > self.PROMPT_INPUT_TIMEOUT:
            self._pending_prompt = None
            return
        self._pending_prompt = None
        new_prompt = message.text.strip()
        self.gemini_chat.set_custom_prompt(new_prompt)
        self.bot.reply_to(message, strings.set_prompt_done_msg)

    # --- Helpers ---

    def _cleanup_expired_pending(self):
        now = time.time()
        PendingAction.delete().where(PendingAction.timestamp < now - self.PENDING_TIMEOUT).execute()

    @staticmethod
    def _build_admin_keyboard(confirm_data, cancel_data):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_confirm_btn, callback_data=confirm_data),
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data=cancel_data),
        )
        return keyboard
