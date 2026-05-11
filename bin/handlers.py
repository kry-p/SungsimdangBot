import telebot
import tenacity

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
    "laftel": strings.laftel_help_msg,
    "bfrss": strings.bfrss_help_msg,
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
            telebot.types.BotCommand("ask_settings", "AI 설정 확인"),
            telebot.types.BotCommand("myid", "내 사용자 ID 확인"),
            telebot.types.BotCommand("ping", "봇 상태 확인"),
            telebot.types.BotCommand("laftel", "라프텔 애니 정보"),
            telebot.types.BotCommand("bfrss", "해외 rss 번역수신"),
        ]
    )


def register_handlers(bot, hub, logger):
    def safe_handler(func):
        def wrapper(message):
            try:
                func(message)
            except Exception:
                logger.log_error(f"Handler {func.__name__} failed for message: {getattr(message, 'text', None)}")
                try:
                    for attempt in tenacity.Retrying(
                        stop=tenacity.stop_after_attempt(3),
                        wait=tenacity.wait_exponential(multiplier=1, min=1, max=8),
                    ):
                        with attempt:
                            bot.reply_to(message, strings.generic_error_msg)
                except tenacity.RetryError:
                    logger.log_error(f"Failed to send error message for {func.__name__} after retries")

        return wrapper

    # Callback query handler
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(query):
        try:
            bot.answer_callback_query(query.id)
        except Exception:
            return
        try:
            if BotFeaturesHub.is_admin_callback(query.data):
                hub.handle_admin_callback(query)
                return
            if BotFeaturesHub.is_laftel_callback(query.data):
                hub.handle_laftel_callback(query)
                return
            result = QUERY_STRINGS.get(query.data)
            if result is not None:
                bot.send_chat_action(query.message.chat.id, "typing")
                bot.send_message(query.message.chat.id, result)
        except Exception:
            logger.log_error(f"Callback handler failed for data: {query.data}")

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
    @safe_handler
    def handle_roulette(message):
        bot.send_message(message.chat.id, hub.random_based_features.russian_roulette(message.chat.id, message.text))

    @bot.message_handler(commands=["shoot"])
    @safe_handler
    def handle_shoot(message):
        bot.send_message(message.chat.id, hub.random_based_features.trig_bullet(message.chat.id))

    @bot.message_handler(commands=["flush_bullet"])
    @safe_handler
    def handle_flush_bullet(message):
        bot.send_message(message.chat.id, hub.random_based_features.russian_roulette(message.chat.id, "roulette 0 0"))

    # Search
    @bot.message_handler(commands=["search"])
    @safe_handler
    def handle_search(message):
        hub.search_handler(message)

    @bot.message_handler(commands=["namu"])
    @safe_handler
    def handle_namu(message):
        bot.reply_to(message, hub.web_manager.namuwiki_search(message), parse_mode="Markdown")

    # Calculator
    @bot.message_handler(commands=["calc"])
    @safe_handler
    def handle_calc(message):
        hub.calculator_handler(message)

    # Gemini Q&A
    @bot.message_handler(
        func=lambda m: m.caption and m.caption.startswith("/ask"),
        content_types=["photo"],
    )
    @safe_handler
    def handle_ask_photo(message):
        hub.ask_handler(message)

    @bot.message_handler(commands=["ask"])
    @safe_handler
    def handle_ask(message):
        hub.ask_handler(message)

    @bot.message_handler(commands=["clear_chat"])
    @safe_handler
    def handle_clear_chat(message):
        hub.clear_chat_handler(message)

    # Laftel
    @bot.message_handler(commands=["laftel"])
    @safe_handler
    def handle_laftel(message):
        hub.laftel.show_portal(message.chat.id)

    # Admin commands
    @bot.message_handler(commands=["allow_chat"])
    @safe_handler
    def handle_allow_chat(message):
        hub.allow_chat_handler(message)

    @bot.message_handler(commands=["deny_chat"])
    @safe_handler
    def handle_deny_chat(message):
        hub.deny_chat_handler(message)

    @bot.message_handler(commands=["ask_settings"])
    @safe_handler
    def handle_ask_settings(message):
        hub.ask_settings_handler(message)

    # D-day
    @bot.message_handler(commands=["dday"])
    @safe_handler
    def handle_dday(message):
        hub.d_day(message)

    # Send translated RSS feed to FASTAPI server
    @bot.message_handler(commands=["bfrss"])
    @safe_handler
    def handle_bfrss(message):
        hub.rss_handler(message)

    # Location
    @bot.message_handler(content_types=["location"])
    @safe_handler
    def handle_location(message):
        hub.geolocation_info(message, message.location.latitude, message.location.longitude)

    # ForceReply handler for custom prompt input
    @bot.message_handler(func=lambda m: m.reply_to_message and m.reply_to_message.text == strings.set_prompt_input_msg)
    @safe_handler
    def handle_prompt_reply(message):
        hub.handle_prompt_reply(message)

    # ForceReply handler for Laftel search
    @bot.message_handler(
        func=lambda m: m.reply_to_message and m.reply_to_message.text == strings.laftel_search_input_msg
    )
    @safe_handler
    def handle_laftel_search_reply(message):
        hub.laftel.handle_search_reply(message)

    # Ordinary message
    @bot.message_handler(content_types=["text"])
    @safe_handler
    def handle_text(message):
        if message.text.startswith("/"):
            return
        logger.log_info("Ordinary message handler working...")
        logger.log_info(f"Message: {message}")
        hub.ordinary_message(message)
