import telebot

from modules.features_hub import BotFeaturesHub
from resources import strings

QUERY_STRINGS = {
    "get_nearby_temp": strings.temperature_help_msg,
    "random_picker": strings.picker_help_msg,
    "russian_roulette": strings.roulette_help_msg,
    "coin_toss": strings.coin_toss_help_msg,
    "geolocation": strings.geolocation_help_msg,
    "dday": strings.day_help_msg,
    "calc": strings.calc_help_msg,
    "ask": strings.ask_help_msg,
    "search": strings.search_help_msg,
    "namu": strings.namu_help_msg,
}


def register_commands(bot):
    bot.set_my_commands(
        [
            telebot.types.BotCommand("help", "도움말"),
            telebot.types.BotCommand("pick", "랜덤 선택"),
            telebot.types.BotCommand("coin_toss", "동전뒤집기"),
            telebot.types.BotCommand("roulette", "러시안 룰렛 장전"),
            telebot.types.BotCommand("shoot", "러시안 룰렛 격발"),
            telebot.types.BotCommand("flush_bullet", "러시안 룰렛 초기화"),
            telebot.types.BotCommand("calc", "계산기"),
            telebot.types.BotCommand("dday", "D-day 계산"),
            telebot.types.BotCommand("search", "검색"),
            telebot.types.BotCommand("namu", "나무위키 검색"),
            telebot.types.BotCommand("ask", "AI 질문"),
            telebot.types.BotCommand("clear_chat", "AI 대화 초기화"),
            telebot.types.BotCommand("myid", "내 사용자 ID 확인"),
            telebot.types.BotCommand("ping", "봇 상태 확인"),
        ]
    )


def register_handlers(bot, hub, logger):
    # Callback query handler
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(query):
        bot.answer_callback_query(query.id)
        if BotFeaturesHub.is_admin_callback(query.data):
            hub.handle_admin_callback(query)
            return
        result = QUERY_STRINGS.get(query.data)
        if result is not None:
            bot.send_chat_action(query.message.chat.id, "typing")
            bot.send_message(query.message.chat.id, result)

    # Bot status
    @bot.message_handler(commands=["ping"])
    def handle_ping(message):
        bot.send_message(message.chat.id, strings.working_msg)

    # User ID
    @bot.message_handler(commands=["myid"])
    def handle_myid(message):
        bot.reply_to(message, strings.myid_msg.format(message.from_user.id))

    # Help
    @bot.message_handler(commands=["start", "help"])
    def handle_help(message):
        bot.send_message(message.chat.id, strings.start_msg, reply_markup=strings.main_keyboard)

    # Random picker
    @bot.message_handler(commands=["pick"])
    def handle_pick(message):
        bot.send_message(message.chat.id, hub.random_based_features.picker(message.text))

    # Coin toss
    @bot.message_handler(commands=["coin_toss"])
    def handle_coin_toss(message):
        bot.send_message(message.chat.id, hub.random_based_features.coin_toss())

    # Russian roulette
    @bot.message_handler(commands=["roulette"])
    def handle_roulette(message):
        bot.send_message(message.chat.id, hub.random_based_features.russian_roulette(message.chat.id, message.text))

    @bot.message_handler(commands=["shoot"])
    def handle_shoot(message):
        bot.send_message(message.chat.id, hub.random_based_features.trig_bullet(message.chat.id))

    @bot.message_handler(commands=["flush_bullet"])
    def handle_flush_bullet(message):
        bot.send_message(message.chat.id, hub.random_based_features.russian_roulette(message.chat.id, "roulette 0 0"))

    # Search
    @bot.message_handler(commands=["search"])
    def handle_search(message):
        hub.search_handler(message)

    @bot.message_handler(commands=["namu"])
    def handle_namu(message):
        bot.reply_to(message, hub.web_manager.namuwiki_search(message), parse_mode="Markdown")

    # Calculator
    @bot.message_handler(commands=["calc"])
    def handle_calc(message):
        hub.calculator_handler(message)

    # Gemini Q&A
    @bot.message_handler(commands=["ask"])
    def handle_ask(message):
        hub.ask_handler(message)

    @bot.message_handler(commands=["clear_chat"])
    def handle_clear_chat(message):
        hub.clear_chat_handler(message)

    # Admin commands
    @bot.message_handler(commands=["allow_chat"])
    def handle_allow_chat(message):
        hub.allow_chat_handler(message)

    @bot.message_handler(commands=["deny_chat"])
    def handle_deny_chat(message):
        hub.deny_chat_handler(message)

    @bot.message_handler(commands=["ask_settings"])
    def handle_ask_settings(message):
        hub.ask_settings_handler(message)

    # D-day
    @bot.message_handler(commands=["dday"])
    def handle_dday(message):
        hub.d_day(message)

    # Location
    @bot.message_handler(content_types=["location"])
    def handle_location(message):
        hub.geolocation_info(message, message.location.latitude, message.location.longitude)

    # Ordinary message
    @bot.message_handler(content_types=["text"])
    def handle_text(message):
        if message.text.startswith("/"):
            return
        logger.log_info("Ordinary message handler working...")
        logger.log_info(f"Message: {message}")
        hub.ordinary_message(message)
