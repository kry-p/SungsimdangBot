# Bot main script
# run this file to operate bot
# Never ending bot polling by David-Lor
# https://gist.github.com/David-Lor/37e0ae02cd7fb1cd01085b2de553dde4


import signal
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

telebot.apihelper.CONNECT_TIMEOUT = 10
telebot.apihelper.READ_TIMEOUT = 30

# Validate required environment variables
config.validate()

# Initialize database
init_db()
migrate_json_to_db()

# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
hub = BotFeaturesHub(bot)
logger = log.Logger()

# Register commands and handlers
telebot.apihelper.RETRY_ON_ERROR = False
try:
    register_commands(bot)
except Exception as e:
    print(f"register_commands failed at startup: {e}", flush=True)
finally:
    telebot.apihelper.RETRY_ON_ERROR = True
register_handlers(bot, hub, logger)

shutdown_event = threading.Event()


def shutdown_handler(signum, frame):
    logger.log_info("Received shutdown signal, stopping...")
    bot.stop_polling()
    shutdown_event.set()


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


def bot_polling():
    logger.log_info("Starts polling")
    while True:
        try:
            logger.log_info("Bot instance is running")
            bot.polling(none_stop=True, skip_pending=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
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
        try:
            hub.gemini_chat.cleanup_expired()
        except Exception as e:
            logger.log_error(f"Cleanup failed: {e}")


polling_thread = threading.Thread(target=bot_polling, daemon=True)
polling_thread.start()

cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    shutdown_event.wait()
