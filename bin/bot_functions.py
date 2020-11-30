# Bot functions script

import random
import sqlite3
import resources
import schedule
import time

from selenium import webdriver
from bs4 import BeautifulSoup
from multiprocessing import Process

TEMPERATURE_URL = 'http://www.koreawqi.go.kr/index_web.jsp'
USER_INFO = './user.db'

userDB = sqlite3.connect(USER_INFO)
cursor = userDB.cursor()


class UserManager:
    # init
    def __init__(self):
        pass


class RiverTempManager:
    #init
    def __init_(self):
        pass

    def update(self):
        pass


class BotFunctions:
    # init
    def __init__(self):
        self.fwordcount = 0
        BotFunctions.driver = webdriver.PhantomJS()
        self.startFtime = 0

    # Get current river temperature (in progress)
    def get_temp(self, user_id):
        print(user_id)
        BotFunctions.driver.get(TEMPERATURE_URL)
        BotFunctions.driver.switch_to.frame('MainFrame')

        html = BotFunctions.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        try:
            hangang_temp = soup.select('tr > td.avg1')[18].text.strip()
            return '현재 한강 수온은 ' + hangang_temp + '도입니다.'
        except AttributeError:
            return '현재 수온 정보를 가져올 수 없습니다..'

    def picker(self, msg):
        random.seed()
        split = msg.split()
        split = [item for item in split if '/pick' not in item]

        try:
            choice = random.choice(split)
        except IndexError:
            return resources.pickerErrorMsg

        return choice

    def coin_toss(self):
        random.seed()
        return '동전뒤집기 결과 : ' + random.choice(resources.coinTossResult)

    def magic_conch(self):
        random.seed()
        init_rand = random.randrange(0, 3)
        return resources.magicConchSentence[init_rand][random.randrange(0, len(resources.magicConchSentence[init_rand]))]

    def RussRoulette(self):
        pass

    def fwordCTup(self):
        if not self.startFtime:
            self.startFtime = time.time()
        self.fwordcount += 1

        if ((time.time() - self.startFtime) <= 600) and self.fwordcount >= 10:
            return '진정좀 하라구 욕이 너무 많아'
        elif ((time.time() - self.startFtime) >= 600) and self.fwordcount <= 10:
            self.startFtime = 0
            self.fwordcount = 0

    def ordinary_message(self, bot, chat_id, message, message_text):

        # location-based message if user sent message that includes '수온' or '자살'
        if ('수온' in message_text) or ('자살' in message_text):
            bot.reply_to(message, BotFunctions.get_temp(self, chat_id))
            #bot.send_message(chat_id, BotFunctions.get_temp(self, chat_id))
        
        # randomly select magic conch message if user sent message that includes '마법의 소라고둥/동'
        if ('마법의 소라고둥' in message_text) or ('마법의 소라고동' in message_text):
            bot.reply_to(message, BotFunctions.magic_conch(self))
            #bot.send_message(chat_id, BotFunctions.magic_conch(self))

        for n in range(len(resources.koreanFWord)):
            if resources.fwordlist[n] in message_text:
                bot.reply_to(message, BotFunctions.fwordCTup(self))
                #bot.send_message(chat_id, BotFunctions.fwordCTup(self))
