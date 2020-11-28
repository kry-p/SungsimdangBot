from time import sleep

import bot_functions
import bot_settings
import strings
import telepot
from telepot.loop import MessageLoop


# Message handler
def main_handler(msg):
    msg_type, chat_type, chat_id, msg_data, msg_id = telepot.glance(msg, long=True)

    if msg_type == 'text':
        if msg['text'] == '/' + 'ping':
            sungsimdangBot.sendMessage(chat_id, strings.working)
        elif msg['text'] == '/' + 'help':
            sungsimdangBot.sendMessage(chat_id, strings.functionList)
        elif msg['text'] == '한강 수온' or '자살' in msg['text']:
            sungsimdangBot.sendMessage(chat_id, botFunctions.get_temp())
        elif msg['text'] == '미구현':
            sungsimdangBot.sendMessage(chat_id, '아직 구현되지 않았습니다.')


# Initialize bot
sungsimdangBot = telepot.Bot(bot_settings.BOT_TOKEN)
botFunctions = bot_functions.BotFunctions()
MessageLoop(sungsimdangBot, main_handler).run_as_thread()

# Loop
while True:
    sleep(100)
