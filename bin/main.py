# Bot main script
# run this file to operate bot
# Never ending bot polling by David-Lor
# https://gist.github.com/David-Lor/37e0ae02cd7fb1cd01085b2de553dde4


# TODO
# 봇이 정지된 동안의 메시지를 한꺼번에 받아서 처리하는 문제가 있습니다.
# 정지된 동안에 수신된 메시지를 무시하도록 관련 처리가 필요합니다.
# 여러 목적으로 활용하기 위한 로그를 작성할 예정입니다.
import logging
import threading
from time import sleep

import telebot

from bin.handlers import register_commands, register_handlers
from config import config
from modules import log
from modules.database import init_db
from modules.features_hub import BotFeaturesHub
from modules.migration import migrate_json_to_db

BOT_INTERVAL = 3
BOT_TIMEOUT = 30
CLEANUP_INTERVAL = 600

# Initialize database
init_db()
migrate_json_to_db()

# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
hub = BotFeaturesHub(bot)
logger = log.Logger()

# Register commands and handlers
register_commands(bot)
register_handlers(bot, hub, logger)


def bot_polling():
    logging.info("Starts polling")
    while True:
        try:
            logger.log_info("Bot instance is running")
            bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
        except Exception as ex:
            logger.log_error(f"Polling has failed. Retry in {BOT_TIMEOUT} sec.\n Error : {ex}\n")
            bot.stop_polling()
            sleep(BOT_TIMEOUT)
        else:
            bot.stop_polling()
            logger.log_info("Polling stopped")
            break


def periodic_cleanup():
    while True:
        sleep(CLEANUP_INTERVAL)
        hub.gemini_chat.cleanup_expired()


polling_thread = threading.Thread(target=bot_polling, daemon=True)
polling_thread.start()

cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    while True:
        try:
            sleep(120)
        except KeyboardInterrupt:
            break
