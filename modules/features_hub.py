# Bot features script

import datetime

from telegramify_markdown import convert, split_entities

from modules import log
from modules.admin import AdminManager
from modules.calculator import Calculator
from modules.gemini_chat import GeminiChat
from modules.laftel import LaftelService
from modules.random_based import RandomBasedFeatures
from modules.utils import strip_html_tags
from modules.web_based import WebManager
from resources import strings

logger = log.Logger()


class BotFeaturesHub:
    @staticmethod
    def is_admin_callback(data):
        return AdminManager.is_admin_callback(data)

    @staticmethod
    def is_laftel_callback(data):
        return LaftelService.is_laftel_callback(data)

    # init
    def __init__(self, bot):
        self.bot = bot

        self.random_based_features = RandomBasedFeatures()
        self.web_manager = WebManager()
        self.calculator = Calculator()
        self.gemini_chat = GeminiChat()
        self.admin = AdminManager(bot, self.gemini_chat)
        self.laftel = LaftelService(bot)

    # --- Admin delegation ---

    @staticmethod
    def is_admin(user_id):
        return AdminManager.is_admin(user_id)

    def handle_admin_callback(self, call):
        self.admin.handle_admin_callback(call)

    def handle_laftel_callback(self, call):
        self.laftel.handle_laftel_callback(call)

    def allow_chat_handler(self, message):
        self.admin.allow_chat_handler(message)

    def deny_chat_handler(self, message):
        self.admin.deny_chat_handler(message)

    def ask_settings_handler(self, message):
        self.admin.ask_settings_handler(message)

    def handle_prompt_reply(self, message):
        self.admin.handle_prompt_reply(message)

    # --- Features ---

    # Get current river temperature
    def get_temp(self):
        self.web_manager.update_suon()
        provided_suon = self.web_manager.provide_suon_v2()

        if provided_suon == strings.suon_maintenance_status:
            return strings.suon_unavailable_msg
        return strings.suon_result_msg.format(provided_suon)

    # D-day
    def d_day(self, message):
        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)

        split = message.text.split()
        split = [item for item in split if "/dday" not in item]

        try:
            split = list(map(int, split))
            dest = datetime.date(split[0], split[1], split[2])

            result = (dest - today).days

            if result == 0:
                self.bot.reply_to(message, strings.day_dest_msg)
            elif result > 0:
                self.bot.reply_to(message, str(result) + strings.day_left_msg)
            elif result < 0:
                self.bot.reply_to(message, str(-1 * result) + strings.day_passed_msg)

        except (ValueError, IndexError):
            self.bot.reply_to(message, strings.day_out_of_range_msg)

    # Geolocation information
    def geolocation_info(self, message, latitude, longitude):
        try:
            result = self.web_manager.geolocation_info(latitude, longitude)
            self.bot.reply_to(message, result)
        except Exception:
            self.bot.reply_to(message, strings.geolocation_error_msg)

    # Search
    def search_handler(self, message):
        try:
            result = self.web_manager.daum_search(message, None)
            result_contents = ""

            for doc in result.documents[:5]:
                link = f"[{strings.search_more_link_msg}]({doc.url})"
                result_contents += strip_html_tags(f"*{doc.title}*\n{doc.contents}\n{link}\n\n")
            text = strings.search_result_header_msg + strip_html_tags(result_contents)
            self.bot.reply_to(message, text, parse_mode="Markdown")
        except Exception:
            self.bot.reply_to(message, strings.search_error_msg)

    # Calculator
    def calculator_handler(self, message):
        parts = message.text.split()
        command = parts[0]

        if len(parts) >= 2:
            actual_text = message.text[len(command) :]

            result = self.calculator.operation(actual_text)

            if result == "syntax error":
                self.bot.reply_to(message, strings.calc_syntax_error_msg)
            elif result == "division by zero error":
                self.bot.reply_to(message, strings.calc_division_by_zero_error_msg)
            else:
                self.bot.reply_to(message, result)

    # Ask handler
    def ask_handler(self, message):
        text = message.text or message.caption or ""
        parts = text.split()
        command = parts[0] if parts else ""
        if len(text.strip()) <= len(command):
            self.bot.reply_to(message, strings.ask_empty_msg)
            return
        question = text[len(command) :].strip()
        language_code = getattr(message.from_user, "language_code", None)

        image = None
        context = None
        photo_list = getattr(message, "photo", None)
        reply = getattr(message, "reply_to_message", None)
        if photo_list:
            image = self._download_photo(photo_list)
            if image is None:
                self.bot.reply_to(message, strings.ask_photo_download_error_msg)
                return
        elif reply:
            reply_photo = getattr(reply, "photo", None)
            if reply_photo:
                image = self._download_photo(reply_photo)
                if image is None:
                    self.bot.reply_to(message, strings.ask_photo_download_error_msg)
                    return
            context = getattr(reply, "text", None) or getattr(reply, "caption", None)

        self.bot.send_chat_action(message.chat.id, "typing")
        result = self.gemini_chat.ask(message.chat.id, message.from_user.id, question, language_code, context, image)
        for chunk in result:
            self._reply_markdown(message, chunk)

    def _download_photo(self, photo_list):
        try:
            file_info = self.bot.get_file(photo_list[-1].file_id)
            return self.bot.download_file(file_info.file_path)
        except Exception:
            logger.log_error("Failed to download photo.")
            return None

    def _reply_markdown(self, message, text):
        try:
            converted_text, entities = convert(text)
            parts = split_entities(converted_text, entities, max_utf16_len=4090)
            for part_text, part_entities in parts:
                self.bot.reply_to(
                    message,
                    part_text,
                    entities=[e.to_dict() for e in part_entities],
                )
        except Exception:
            logger.log_error("Markdown conversion failed, sending as plain text.")
            for plain_chunk in GeminiChat.split_response(text):
                self.bot.reply_to(message, plain_chunk)

    # Clear chat
    def clear_chat_handler(self, message):
        self.gemini_chat.clear_session(message.chat.id, message.from_user.id)
        self.bot.reply_to(message, strings.ask_clear_msg)

    # Handling ordinary message
    def ordinary_message(self, message):
        if ("수온" in message.text) or ("자살" in message.text):
            self.bot.reply_to(message, self.get_temp())

        if ("마법의 소라고둥" in message.text) or ("마법의 소라고동" in message.text):
            self.bot.reply_to(message, self.random_based_features.magic_conch())
