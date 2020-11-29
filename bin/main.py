from time import sleep

import bot_functions
import bot_settings
import strings
import telepot
import telebot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# commands
CMD_PING = '/ping'
CMD_PICK = '/pick'
CMD_HELP = '/help'
CMD_USER_MANAGER = '/user_manager'

# # Message handler
# def main_handler(msg):
#     msg_type, chat_type, chat_id, msg_data, msg_id = telepot.glance(msg, long=True)
#
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text='가까운 강 수온 정보', callback_data='nearby_river_temp'),
#          InlineKeyboardButton(text='랜덤픽', callback_data='select_one')],
#         [InlineKeyboardButton(text='러시안 룰렛', callback_data='russian_roulette'),
#          InlineKeyboardButton(text='도움말', callback_data='help')]
#     ])
#
#     sungsimdangBot.sendMessage(chat_id, strings.start, reply_markup=keyboard)
#
#     if msg_type == 'text':
#         if CMD_PING in msg['text']:
#             sungsimdangBot.sendMessage(chat_id, strings.working)
#
#         elif CMD_HELP in msg['text']:
#             sungsimdangBot.sendMessage(chat_id, strings.functionList)
#
#         elif msg['text'] == '한강 수온' or '자살' in msg['text']:
#             sungsimdangBot.sendMessage(chat_id, botFunctions.get_temp())
#
#         elif CMD_PICK in msg['text']:
#             sungsimdangBot.sendMessage(chat_id, botFunctions.picker(msg['text']))
#
#         elif msg['text'] == '미구현':
#             sungsimdangBot.sendMessage(chat_id, '아직 구현되지 않았습니다.')
#
#
# def query_handler(msg):
#     query_id, from_id, query_data = telepot.glance(msg, long=True, flavor='callback_query')
#     print('Callback Query:', query_id, from_id, query_data)


# Initialize bot

# sungsimdangBot = telepot.Bot(bot_settings.BOT_TOKEN)
botFunctions = bot_functions.BotFunctions()
# userManager = bot_functions.UserManager()
# mainLoop = MessageLoop(sungsimdangBot, {'chat': main_handler,
#                                         'callback_query': query_handler})
# mainLoop.run_forever()

# Loop
# while True:
#     sleep(100)

# Telebot

sungsimdangBot = telebot.TeleBot(bot_settings.BOT_TOKEN, parse_mode=None)


@sungsimdangBot.message_handler(commands=['start'])
def start_command(message):
    sungsimdangBot.send_message(
        message.chat.id, strings.start
    )


# Handles all text messages that match the regular expression
@sungsimdangBot.message_handler(regexp="한강 수온")
def handle_message(message):
    print(message)
    sungsimdangBot.send_message(
        message.chat.id, botFunctions.get_temp()
    )


sungsimdangBot.polling(none_stop=True)