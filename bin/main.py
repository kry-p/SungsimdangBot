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
        data = query.data
        MessageProvider.get_ex_callback(query)
    
    def get_ex_callback(query):
        sungsimdangBot.answer_callback_query(query.id)
        MessageProvider.send_query_result(query.message)

    def send_query_result(message):
        sungsimdangBot.send_chat_action(message.chat.id, 'typing')
        sungsimdangBot.send_message(
            message.chat.id, '결과 예시입니다.'
        )
    
    # check bot status
    @sungsimdangBot.message_handler(commands=['ping'])
    def start_command(message):
        sungsimdangBot.send_message(message.chat.id, resources.workingMsg)

    # message for /help
    @sungsimdangBot.message_handler(commands=['help'])
    def start_command(message):
        sungsimdangBot.send_message(message.chat.id, resources.functionListMsg)

    # message for /start
    @sungsimdangBot.message_handler(commands=['start'])
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
        
    # ordinary message handler
    @sungsimdangBot.message_handler(content_types=['text'])
    def handle_message(message):
        # check if message is command
        if message.text.startswith('/'):
            return
        else:
            print('ordinary message handler working')
            botFunctions.ordinary_message(sungsimdangBot, message.chat.id, message, message.text)

        # a[0][] == 김사각  -> b[0][0] == 야구 그만봐 [0][1] 게임 그만해 [0][2] 진정하자
 

sungsimdangBot.polling(none_stop=True)
