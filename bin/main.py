# Bot main script
# run this file to operate bot

# TODO
# 봇이 정지된 동안의 메시지를 한꺼번에 받아서 처리하는 문제가 있습니다.
# 정지된 동안에 수신된 메시지를 무시하도록 관련 처리가 필요합니다.

import bot_functions
import bot_settings
import resources
import telebot

# Initialize bot

sungsimdangBot = telebot.TeleBot(bot_settings.BOT_TOKEN, parse_mode=None)
botFunctions = bot_functions.BotFunctions()


# Message handler
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
        if query.data == 'random_picker':
            sungsimdangBot.send_message(message.chat.id, resources.pickerHelpMsg)
        elif query.data == 'get_nearby_temp':
            sungsimdangBot.send_message(message.chat.id, resources.temperatureHelpMsg)
        elif query.data == 'russian_roulette':
            sungsimdangBot.send_message(message.chat.id, resources.rouletteHelpMsg)
        elif query.data == 'coin_toss':
            sungsimdangBot.send_message(message.chat.id, resources.coinTossHelpMsg)
        elif query.data == 'gaechu_info':
            sungsimdangBot.send_message(message.chat.id, resources.gaechuInfoHelpMsg)
    
    # check bot status
    @sungsimdangBot.message_handler(commands=['ping'])
    def start_command(message):
        sungsimdangBot.send_message(message.chat.id, resources.workingMsg)

    # message for /start
    @sungsimdangBot.message_handler(commands=['start', 'help'])
    def exchange_command(message):
        sungsimdangBot.send_message(message.chat.id, resources.startMsg, reply_markup=resources.mainKeyboard)

    # randomly select one word between 1 or more words
    @sungsimdangBot.message_handler(commands=['pick'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFunctions.picker(message.text))

    # randomly select coin heads or tails
    @sungsimdangBot.message_handler(commands=['coin_toss'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFunctions.coin_toss())

    @sungsimdangBot.message_handler(commands=['roulette'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFunctions.russian_roulette(message.text))

    @sungsimdangBot.message_handler(commands=['shoot'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFunctions.trig_bullet())

    @sungsimdangBot.message_handler(commands=['flush_bullet'])
    def handle_message(message):
        sungsimdangBot.send_message(message.chat.id, botFunctions.russian_roulette('roulette 0 0'))
        
    # ordinary message handler
    @sungsimdangBot.message_handler(content_types=['text'])
    def handle_message(message):
        # check if message is command
        if message.text.startswith('/'):
            return
        else:
            print('ordinary message handler working')
            botFunctions.ordinary_message(sungsimdangBot, message.chat.id, message)


sungsimdangBot.polling(none_stop=True)
