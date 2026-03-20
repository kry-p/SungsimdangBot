# Bot features script

import datetime
import json
import urllib.parse

import requests
import telebot

from config import config
from modules.calculator import Calculator
from modules.gemini_chat import GeminiChat
from modules.random_based import RandomBasedFeatures
from modules.web_based import WebManager
from resources import strings

MAP_BASE_URL = "https://dapi.kakao.com/v2/local/geo/coord2address.json?"
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"


class BotFeaturesHub:
    # init
    def __init__(self, bot):
        self.bot = bot

        self.random_based_features = RandomBasedFeatures()
        self.web_manager = WebManager()
        self.calculator = Calculator()
        self.gemini_chat = GeminiChat()
        self.pending_actions = {}

    # Get current river temperature 현재 강물 온도 정보 획득
    def get_temp(self, user_id):
        self.web_manager.update_suon()
        provided_suon = self.web_manager.provide_suon_v2()

        if provided_suon == "점검중":
            return strings.suon_unavailable_msg
        return strings.suon_result_msg.format(provided_suon)

    # D-day
    def d_day(self, message):
        now = datetime.datetime.now()  # today
        today = datetime.date(now.year, now.month, now.day)

        split = message.text.split()
        split = [item for item in split if "/dday" not in item]

        try:
            split = list(map(int, split))  # String to calculable integer values
            dest = datetime.date(split[0], split[1], split[2])  # date that user entered

            result = (dest - today).days

            if result == 0:
                self.bot.reply_to(message, strings.day_dest_msg)
            elif result > 0:
                self.bot.reply_to(message, str(result) + strings.day_left_msg)
            elif result < 0:
                self.bot.reply_to(message, str(-1 * result) + strings.day_passed_msg)

        except (ValueError, IndexError):  # wrong input
            self.bot.reply_to(message, strings.day_out_of_range_msg)

    # Geolocation information　위치 기반 정보 제공
    def geolocation_info(self, message, latitude, longitude):
        try:
            # location info
            map_args = {"x": longitude, "y": latitude}
            map_url = MAP_BASE_URL + urllib.parse.urlencode(map_args)
            map_headers = {"Authorization": "KakaoAK " + config.KAKAO_TOKEN}
            map_request = requests.get(map_url, headers=map_headers, timeout=10)

            # weather info (by OpenWeatherMap)
            weather_args = {"lang": "kr", "appid": config.WEATHER_TOKEN, "lat": latitude, "lon": longitude}
            weather_url = WEATHER_BASE_URL + urllib.parse.urlencode(weather_args)
            weather_request = requests.get(weather_url, timeout=10)
            weather_json = json.loads(weather_request.text)

            # temporarily store weather info
            weather = weather_json["weather"][0]["description"]
            temp = str(round(weather_json["main"]["temp"] - 273.15)) + "°C"
            feels_temp = str(round(weather_json["main"]["feels_like"] - 273.15)) + "°C"
            humidity = str(round(weather_json["main"]["humidity"])) + "%"

            # makes script and sends message
            weather_result = (
                "날씨 " + weather + ", " + "기온 " + temp + ", " + "체감온도 " + feels_temp + ", " + "습도 " + humidity
            )

            map_location = json.loads(map_request.text)["documents"][0]["address"]["address_name"]
            geo_location = "위도 : " + str(latitude) + ", 경도 : " + str(longitude)

            result = geo_location + "\n" + map_location + "\n\n" + weather_result

            self.bot.reply_to(message, result)
        except Exception:
            self.bot.reply_to(message, strings.geolocation_error_msg)

    # Calculator 계산기
    def calculator_handler(self, message):
        # cut command string
        command = message.text.split()[0]

        if len(message.text.split()) >= 2:
            actual_text = message.text[len(command) :]

            # calculate
            result = self.calculator.operation(actual_text)

            # error handling
            if result == "syntax error":
                self.bot.reply_to(message, strings.calc_syntax_error_msg)
            elif result == "division by zero error":
                self.bot.reply_to(message, strings.calc_division_by_zero_error_msg)
            else:
                self.bot.reply_to(message, result)

    # Ask handler AI 질문
    def ask_handler(self, message):
        command = message.text.split()[0]
        if len(message.text.strip()) <= len(command):
            self.bot.reply_to(message, strings.ask_empty_msg)
            return
        question = message.text[len(command) :].strip()
        language_code = getattr(message.from_user, "language_code", None)
        self.bot.send_chat_action(message.chat.id, "typing")
        result = self.gemini_chat.ask(message.chat.id, question, language_code)
        if isinstance(result, list):
            for chunk in result:
                self.bot.reply_to(message, chunk)
        else:
            self.bot.reply_to(message, result)

    # Clear chat 대화 초기화
    def clear_chat_handler(self, message):
        self.gemini_chat.clear_session(message.chat.id)
        self.bot.reply_to(message, strings.ask_clear_msg)

    # Admin check 관리자 확인
    @staticmethod
    def is_admin(user_id):
        return user_id == config.ADMIN_USER_ID

    # Allow chat 채팅 허용
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
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_confirm_btn, callback_data="allow_confirm:0"),
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data="allow_cancel:0"),
        )
        sent = self.bot.reply_to(
            message,
            strings.admin_allow_confirm_msg.format(name=name or chat_id, chat_id=chat_id),
            reply_markup=keyboard,
        )
        msg_id = sent.message_id
        self.pending_actions[msg_id] = {"action": "allow", "chat_id": chat_id, "name": name}
        self.bot.edit_message_reply_markup(
            sent.chat.id,
            msg_id,
            reply_markup=self._build_admin_keyboard(f"allow_confirm:{msg_id}", f"allow_cancel:{msg_id}"),
        )

    # Deny chat 채팅 거부
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
        if chat_id not in self.gemini_chat.allowlist:
            self.bot.reply_to(message, strings.admin_deny_chat_not_found_msg.format(chat_id=chat_id))
            return
        name = self.gemini_chat.allowlist[chat_id]
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_confirm_btn, callback_data="deny_confirm:0"),
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data="deny_cancel:0"),
        )
        sent = self.bot.reply_to(
            message,
            strings.admin_deny_confirm_msg.format(name=name or chat_id, chat_id=chat_id),
            reply_markup=keyboard,
        )
        msg_id = sent.message_id
        self.pending_actions[msg_id] = {"action": "deny", "chat_id": chat_id, "name": name}
        self.bot.edit_message_reply_markup(
            sent.chat.id,
            msg_id,
            reply_markup=self._build_admin_keyboard(f"deny_confirm:{msg_id}", f"deny_cancel:{msg_id}"),
        )

    # Admin callback 관리자 콜백 처리
    def handle_admin_callback(self, call):
        if not self.is_admin(call.from_user.id):
            return
        action, msg_id_str = call.data.split(":", 1)
        msg_id = int(msg_id_str)
        pending = self.pending_actions.pop(msg_id, None)
        if not pending:
            return
        chat_id = pending["chat_id"]
        name = pending["name"]
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

    @staticmethod
    def _build_admin_keyboard(confirm_data, cancel_data):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.admin_confirm_btn, callback_data=confirm_data),
            telebot.types.InlineKeyboardButton(strings.admin_cancel_btn, callback_data=cancel_data),
        )
        return keyboard

    # List chats 허용 목록 조회
    def list_chats_handler(self, message):
        if not self.is_admin(message.from_user.id):
            self.bot.reply_to(message, strings.admin_only_msg)
            return
        chats = self.gemini_chat.list_allowed_chats()
        if not chats:
            self.bot.reply_to(message, strings.admin_list_chats_empty_msg)
        else:
            chat_list = "\n".join(f"{c['id']} ({c['name']})" if c["name"] else str(c["id"]) for c in chats)
            self.bot.reply_to(message, strings.admin_list_chats_msg.format(chat_list))

    # Handling ordinary message 일반 메시지 처리
    def ordinary_message(self, message):
        # location-based message if user sent message that includes '수온' or '자살'
        if ("수온" in message.text) or ("자살" in message.text):
            self.bot.reply_to(message, self.get_temp(message.from_user.id))

        # randomly select magic conch message if user sent message that includes '마법의 소라고둥/동'
        if ("마법의 소라고둥" in message.text) or ("마법의 소라고동" in message.text):
            self.bot.reply_to(message, self.random_based_features.magic_conch())
