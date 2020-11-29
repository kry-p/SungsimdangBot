import bot_functions
import bot_settings
import strings
import telebot

# commands
CMD_PING = '/ping'
CMD_PICK = '/pick'
CMD_HELP = '/help'
CMD_USER_MANAGER = '/user_manager'

# Initialize bot

sungsimdangBot = telebot.TeleBot(bot_settings.BOT_TOKEN, parse_mode=None)
botFunctions = bot_functions.BotFunctions()


# Message handler
class MessageProvider:
    def __init__(self):
        pass

    # message for /help
    @sungsimdangBot.message_handler(commands=['help'])
    def start_command(message):
        sungsimdangBot.send_message(
            message.chat.id, strings.functionList
        )

    # message for /start
    @sungsimdangBot.message_handler(commands=['start'])
    def start_command(message):
        sungsimdangBot.send_message(
            message.chat.id, strings.start
        )

    # location-based message if user sent message that includes '수온' or '자살'
    @sungsimdangBot.message_handler(regexp='[.수온.|.자살.]')
    def handle_message(message):
        sungsimdangBot.send_message(
            message.chat.id, botFunctions.get_temp(message.chat.id)
        )

    # randomly select one text between 1 or more words
    @sungsimdangBot.message_handler(regexp='[/pick.]')
    def handle_message(message):
        sungsimdangBot.send_message(
            message.chat.id, botFunctions.picker(message.text)
        )


sungsimdangBot.polling(none_stop=True)
