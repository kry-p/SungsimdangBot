import telebot

BOT_POLLING_INTERVAL = 3
BOT_REQUEST_TIMEOUT = 30
BOT_LONG_POLLING_TIMEOUT = 20


def create_bot(token):
    return telebot.TeleBot(token, parse_mode=None, skip_pending=True)


def run_polling(bot, logger):
    logger.add_file_handler_to(telebot.logger)
    logger.log_info("Starts polling")
    logger.log_info("Bot instance is running")
    bot.infinity_polling(
        interval=BOT_POLLING_INTERVAL,
        timeout=BOT_REQUEST_TIMEOUT,
        long_polling_timeout=BOT_LONG_POLLING_TIMEOUT,
    )
    logger.log_info("Polling stopped")
