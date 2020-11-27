import telepot
import bot_settings
import strings
from telepot.loop import MessageLoop
from time import sleep


class BotFunctions:
    def __init__(self):
        pass

    def get_temp(self):
        return '현재 한강 수온은 11.4도 입니다.'


def main_handler(msg):
    msg_type, chat_type, chat_id, msg_data, msg_id = telepot.glance(msg, long=True)
    print(msg)

    if msg_type == 'text':
        if msg['text'] == '/' + 'ping':
            sungsimdangBot.sendMessage(chat_id, strings.working)
        elif msg['text'] == '/' + 'help':
            sungsimdangBot.sendMessage(chat_id, strings.functionList)
        elif msg['text'] == '한강 수온':
            sungsimdangBot.sendMessage(chat_id, botFunctions.get_temp())
        elif msg['text'] == '미구현':
            sungsimdangBot.sendMessage(chat_id, '아직 구현되지 않았습니다.')


sungsimdangBot = telepot.Bot(bot_settings.BOT_TOKEN)
botFunctions = BotFunctions()
MessageLoop(sungsimdangBot, main_handler).run_as_thread()

while True:
    sleep(100)
