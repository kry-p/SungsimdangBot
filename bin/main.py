# Bot main script
# run this file to operate bot

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
from modules.polling import create_bot, run_polling

CLEANUP_INTERVAL = 600

telebot.apihelper.CONNECT_TIMEOUT = 10
telebot.apihelper.READ_TIMEOUT = 30


def shutdown_handler(signum, frame, bot, logger, shutdown_event):
    logger.log_info("Received shutdown signal, stopping...")
    bot.stop_polling()
    shutdown_event.set()


def periodic_cleanup(hub, logger):
    while True:
        sleep(CLEANUP_INTERVAL)
        try:
            hub.ai_chat.cleanup_expired()
        except Exception as e:
            logger.log_error(f"Cleanup failed: {e}")


def main():
    config.validate()

    init_db()
    migrate_json_to_db()

    bot = create_bot(config.BOT_TOKEN)
    hub = BotFeaturesHub(bot)
    logger = log.Logger()

    telebot.apihelper.RETRY_ON_ERROR = False
    try:
        register_commands(bot)
    except Exception as e:
        print(f"register_commands failed at startup: {e}", flush=True)
    finally:
        telebot.apihelper.RETRY_ON_ERROR = True
    register_handlers(bot, hub, logger)

    shutdown_event = threading.Event()

    def handle_shutdown(signum, frame):
        shutdown_handler(signum, frame, bot, logger, shutdown_event)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    polling_thread = threading.Thread(target=run_polling, args=(bot, logger), daemon=True)
    polling_thread.start()

    cleanup_thread = threading.Thread(target=periodic_cleanup, args=(hub, logger), daemon=True)
    cleanup_thread.start()

    shutdown_event.wait()


if __name__ == "__main__":
    main()
