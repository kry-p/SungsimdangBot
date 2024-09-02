# Bot main script
# run this file to operate bot
# Never ending bot polling by David-Lor
# https://gist.github.com/David-Lor/37e0ae02cd7fb1cd01085b2de553dde4


# TODO
# 봇이 정지된 동안의 메시지를 한꺼번에 받아서 처리하는 문제가 있습니다.
# 정지된 동안에 수신된 메시지를 무시하도록 관련 처리가 필요합니다.
# 여러 목적으로 활용하기 위한 로그를 작성할 예정입니다.
import os
import sys
import logging
import logging.handlers

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from modules import features_hub
from modules import log
from config import config
from resources import strings
import telebot
import threading
import re
from time import sleep

BOT_INTERVAL = 3
BOT_TIMEOUT = 30


# Initialize bot
sungsimdangBot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
botFeatures = features_hub.BotFeaturesHub(sungsimdangBot)

# Initialize logger module
logger = log.Logger()

def bot_polling():
    logging.info("Starts polling")
    while True:
        try:
            logger.log_info("Bot instance is running")
            sungsimdangBot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
        except Exception as ex:  # Error in polling
            logger.log_error("Polling has failed. Retry in {} sec.\n Error : {}\n".format(BOT_TIMEOUT, ex))
            sungsimdangBot.stop_polling()
            sleep(BOT_TIMEOUT)
        else:  # Clean exit
            sungsimdangBot.stop_polling()
            logger.log_info("Polling stopped")
            break  # End loop


# Callback query strings
query_string = {
    'get_nearby_temp': strings.temperatureHelpMsg,
    'random_picker': strings.pickerHelpMsg,
    'russian_roulette': strings.rouletteHelpMsg,
    'coin_toss': strings.coinTossHelpMsg,
    'bad_word_detector': strings.badWordDetectorHelpMsg,
    'geolocation': strings.geolocationHelpMsg,
    'dday': strings.dayHelpMsg,
    'calc': strings.calcHelpMsg
}


# Message handler 메시지 처리
class MessageProvider:
    def __init__(self):
        pass

    # callback query handler
    @sungsimdangBot.callback_query_handler(func=lambda call: True)
    def iq_callback(query):
        MessageProvider.get_ex_callback(query)

    def get_ex_callback(query):
        sungsimdangBot.answer_callback_query(query.id)
        MessageProvider.send_query_result(query, query.message)

    # launch command or show help message
    def send_query_result(query, message):
        sungsimdangBot.send_chat_action(message.chat.id, 'typing')
        sungsimdangBot.send_message(message.chat.id, query_string[query.data])

    # check bot status
    @sungsimdangBot.message_handler(commands=['ping'])
    def start_command(message):
        sungsimdangBot.send_message(message.chat.id, strings.workingMsg)

    # message for /start
    @sungsimdangBot.message_handler(commands=['start', 'help'])
    def exchange_command(message):
        sungsimdangBot.send_message(message.chat.id, strings.startMsg, reply_markup=strings.mainKeyboard)

    # randomly select one word between 1 or more words
    @sungsimdangBot.message_handler(commands=['pick'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFeatures.randomBasedFeatures.picker(message.text))

    # randomly select coin heads or tails
    @sungsimdangBot.message_handler(commands=['coin_toss'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFeatures.randomBasedFeatures.coin_toss())

    # Russian roulette
    @sungsimdangBot.message_handler(commands=['roulette'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFeatures.randomBasedFeatures.russian_roulette(message.text))

    @sungsimdangBot.message_handler(commands=['shoot'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFeatures.randomBasedFeatures.trig_bullet())

    @sungsimdangBot.message_handler(commands=['flush_bullet'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFeatures.randomBasedFeatures.russian_roulette('roulette 0 0'))

    @sungsimdangBot.message_handler(commands=['search'])
    def handle_message(message):
        result = botFeatures.webManager.daum_search(message, None)
        result_contents = ""

        if len(result['documents']) > 4:
            for i in range(5):
                result_contents += re.sub('<.+?>', '', "*" + result['documents'][i]['title']
                                          + "*\n" + result['documents'][i]['contents']
                                          + "\n" + "[더 보기](" + result['documents'][i]['url']
                                          + ")\n\n", 0, re.I | re.S)
        else:
            for i in result['documents']:
                result_contents += re.sub('<.+?>', '', "*" + i['title'] + "*\n"
                                          + i['contents'] + "\n" + "[더 보기]("
                                          + i['url'] + ")\n\n", 0, re.I | re.S)
        text = "검색 결과입니다.\n\n" + re.sub('<.+?>', '', result_contents, 0, re.I | re.S)
        sungsimdangBot.reply_to(message, text, parse_mode="Markdown")

    @sungsimdangBot.message_handler(commands=['namu'])
    def handle_message(message):
        sungsimdangBot.reply_to(message,
                                botFeatures.webManager.namuwiki_search(message),
                                parse_mode="Markdown")

    # calculator
    @sungsimdangBot.message_handler(commands=['calc'])
    def handle_message(message):
        botFeatures.calculator_handler(message)

    # D-day
    @sungsimdangBot.message_handler(commands=['dday'])
    def handle_message(message):
        botFeatures.d_day(message)

    # location
    @sungsimdangBot.message_handler(content_types=['location'])
    def handle_location(message):
        # latitude : 위도, longitude : 경도
        botFeatures.geolocation_info(message, message.location.latitude, message.location.longitude)

    # ordinary message handler
    @sungsimdangBot.message_handler(content_types=['text'])
    def handle_message(message):
        # check if message is command
        if message.text.startswith('/'):
            return
        else:
            logger.log_info('Ordinary message handler working...')
            logger.log_info('Message: {}'.format(message))
            botFeatures.ordinary_message(message)


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
