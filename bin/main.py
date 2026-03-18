# Bot main script
# run this file to operate bot
# Never ending bot polling by David-Lor
# https://gist.github.com/David-Lor/37e0ae02cd7fb1cd01085b2de553dde4


# TODO
# 봇이 정지된 동안의 메시지를 한꺼번에 받아서 처리하는 문제가 있습니다.
# 정지된 동안에 수신된 메시지를 무시하도록 관련 처리가 필요합니다.
# 여러 목적으로 활용하기 위한 로그를 작성할 예정입니다.
import logging
import logging.handlers
import re
import threading
from time import sleep

import telebot

from config import config
from modules import features_hub, log
from resources import strings

BOT_INTERVAL = 3
BOT_TIMEOUT = 30


# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
bot_features = features_hub.BotFeaturesHub(bot)

# Initialize logger module
logger = log.Logger()


def bot_polling():
    logging.info("Starts polling")
    while True:
        try:
            logger.log_info("Bot instance is running")
            bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
        except Exception as ex:  # Error in polling
            logger.log_error(f"Polling has failed. Retry in {BOT_TIMEOUT} sec.\n Error : {ex}\n")
            bot.stop_polling()
            sleep(BOT_TIMEOUT)
        else:  # Clean exit
            bot.stop_polling()
            logger.log_info("Polling stopped")
            break  # End loop


# Callback query strings
query_string = {
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


# Message handler 메시지 처리
class MessageProvider:
    def __init__(self):
        pass

    # callback query handler
    @bot.callback_query_handler(func=lambda call: True)
    def iq_callback(query):
        MessageProvider.get_ex_callback(query)

    def get_ex_callback(query):
        bot.answer_callback_query(query.id)
        MessageProvider.send_query_result(query, query.message)

    # launch command or show help message
    def send_query_result(query, message):
        result = query_string.get(query.data)
        if result is None:
            return
        bot.send_chat_action(message.chat.id, "typing")
        bot.send_message(message.chat.id, result)

    # check bot status
    @bot.message_handler(commands=["ping"])
    def start_command(message):
        bot.send_message(message.chat.id, strings.working_msg)

    # get user id
    @bot.message_handler(commands=["myid"])
    def handle_myid(message):
        bot.reply_to(message, strings.myid_msg.format(message.from_user.id))

    # message for /start
    @bot.message_handler(commands=["start", "help"])
    def exchange_command(message):
        bot.send_message(message.chat.id, strings.start_msg, reply_markup=strings.main_keyboard)

    # randomly select one word between 1 or more words
    @bot.message_handler(commands=["pick"])
    def handle_pick(message):
        bot.send_message(message.chat.id, bot_features.random_based_features.picker(message.text))

    # randomly select coin heads or tails
    @bot.message_handler(commands=["coin_toss"])
    def handle_coin_toss(message):
        bot.send_message(message.chat.id, bot_features.random_based_features.coin_toss())

    # Russian roulette
    @bot.message_handler(commands=["roulette"])
    def handle_roulette(message):
        bot.send_message(
            message.chat.id, bot_features.random_based_features.russian_roulette(message.chat.id, message.text)
        )

    @bot.message_handler(commands=["shoot"])
    def handle_shoot(message):
        bot.send_message(message.chat.id, bot_features.random_based_features.trig_bullet(message.chat.id))

    @bot.message_handler(commands=["flush_bullet"])
    def handle_flush_bullet(message):
        bot.send_message(
            message.chat.id, bot_features.random_based_features.russian_roulette(message.chat.id, "roulette 0 0")
        )

    @bot.message_handler(commands=["search"])
    def handle_search(message):
        try:
            result = bot_features.web_manager.daum_search(message, None)
            result_contents = ""

            for doc in result["documents"][:5]:
                result_contents += re.sub(
                    "<.+?>",
                    "",
                    "*" + doc["title"] + "*\n" + doc["contents"] + "\n" + "[더 보기](" + doc["url"] + ")\n\n",
                    count=0,
                    flags=re.IGNORECASE | re.DOTALL,
                )
            text = strings.search_result_header_msg + re.sub(
                "<.+?>", "", result_contents, count=0, flags=re.IGNORECASE | re.DOTALL
            )
            bot.reply_to(message, text, parse_mode="Markdown")
        except Exception:
            bot.reply_to(message, strings.search_error_msg)

    @bot.message_handler(commands=["namu"])
    def handle_namu(message):
        bot.reply_to(message, bot_features.web_manager.namuwiki_search(message), parse_mode="Markdown")

    # calculator
    @bot.message_handler(commands=["calc"])
    def handle_calc(message):
        bot_features.calculator_handler(message)

    # Gemini Q&A
    @bot.message_handler(commands=["ask"])
    def handle_ask(message):
        bot_features.ask_handler(message)

    @bot.message_handler(commands=["clear_chat"])
    def handle_clear_chat(message):
        bot_features.clear_chat_handler(message)

    # Admin commands
    @bot.message_handler(commands=["allow_chat"])
    def handle_allow_chat(message):
        bot_features.allow_chat_handler(message)

    @bot.message_handler(commands=["deny_chat"])
    def handle_deny_chat(message):
        bot_features.deny_chat_handler(message)

    @bot.message_handler(commands=["list_chats"])
    def handle_list_chats(message):
        bot_features.list_chats_handler(message)

    # D-day
    @bot.message_handler(commands=["dday"])
    def handle_dday(message):
        bot_features.d_day(message)

    # location
    @bot.message_handler(content_types=["location"])
    def handle_location(message):
        # latitude : 위도, longitude : 경도
        bot_features.geolocation_info(message, message.location.latitude, message.location.longitude)

    # ordinary message handler
    @bot.message_handler(content_types=["text"])
    def handle_text(message):
        # check if message is command
        if message.text.startswith("/"):
            return
        else:
            logger.log_info("Ordinary message handler working...")
            logger.log_info(f"Message: {message}")
            bot_features.ordinary_message(message)


polling_thread = threading.Thread(target=bot_polling)
polling_thread.daemon = True
polling_thread.start()

# Keep main program running while bot runs threaded 봇이 스레드에서 작동될 동안 메인 프로그램을 유지
if __name__ == "__main__":
    while True:
        try:
            sleep(120)
        except KeyboardInterrupt:
            break
