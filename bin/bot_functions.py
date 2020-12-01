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
    # init
    def __init__(self, driver):
        self.driver = driver
        self.driver.get(TEMPERATURE_URL)
        self.driver.switch_to.frame('MainFrame')

        self.html = self.driver.page_source
        self.soup = BeautifulSoup(self.html, 'html.parser')

        self.suon = list()
        self.site = list()

    # Update current temperature data
    def update(self):
        site_temp = self.soup.select("tr[class^='site'] > th")
        suon_temp = self.soup.select('tr > td.avg1')

        for i in site_temp:
            self.site.append(i.text.strip())
        for i in suon_temp:
            self.suon.append(i.text.strip())

    # Provide temperature data to other methods
    def provide(self, site):
        try:
            position = self.site.index(site)
            return self.suon[position]
        except ValueError:
            return 'error'


class BotFunctions:
    # init
    def __init__(self):

        BotFunctions.driver = webdriver.PhantomJS()
        self.fwordcount = 0
        self.startFtime = 0
        self.Bullet = ()

        self.riverTempManager = RiverTempManager(BotFunctions.driver)
        self.riverTempManager.update()

        #schedule.every(10).minutes.do(self.riverTempManager.update())

        #while True:
        #    schedule.run_pending()
        #    time.sleep(1)

    # Get current river temperature (in progress)
    def get_temp(self, user_id):
        site = ''
        alias = ''
        self.riverTempManager.update()

        try:
            for user in resources.user:
                if user[0] == str(user_id):
                    site = user[2]
                    alias = user[3]
        except IndexError:
            pass

        result = self.riverTempManager.provide(site)
        try:
            if result == 'error':
                return resources.tempErrorMsg
            else:
                return '현재 ' + alias + ' 수온은 ' + self.riverTempManager.provide(site) + '도입니다.'
        except AttributeError:
            return '현재 한강 수온은 ' + self.riverTempManager.provide('구리') + '도입니다.'

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
        return resources.magicConchSentence[init_rand][
            random.randrange(0, len(resources.magicConchSentence[init_rand]))]

    def RussRoulette(self, msg):
        try:
            if msg.split()[1].isdigit() and msg.split()[2].isdigit():
                self.Bullet = list()
                for n in range(int(msg.split()[1])):
                    self.Bullet.append(False)
                for n in range(int(msg.split()[2])):
                    self.Bullet[n] = True
                random.shuffle(self.Bullet)
                print(self.Bullet)
                return '{}발이 장전되었습니다.'.format(len(self.Bullet))
        except IndexError:
            return '명령어를 형식에 맞게 입력해주세요 \n(ex. /roulette 7 3 장전탄수, 당첨탄수)'

    def TrigBullet(self):
        if len(self.Bullet) == 0:
            return '/roulette 명령어를 사용해 먼저 장전해주세요.'
        check = self.Bullet.pop()
        if check:
            return '실탄'
        else:
            return '공포탄'

    def fwordCTup(self):
        if not self.startFtime:
            self.startFtime = time.time()
        self.fwordcount += 1

        if ((time.time() - self.startFtime) <= 600) and self.fwordcount >= 10:
            return '진정좀 하라구 욕이 너무 많아'
        elif ((time.time() - self.startFtime) >= 600) and self.fwordcount <= 10:
            self.startFtime = 0
            self.fwordcount = 0

    def ordinary_message(self, bot, chat_id, message):
        print(message)

        # location-based message if user sent message that includes '수온' or '자살'
        if ('수온' in message.text) or ('자살' in message.text):
            bot.reply_to(message, BotFunctions.get_temp(self, message.from_user.id))

        # randomly select magic conch message if user sent message that includes '마법의 소라고둥/동'
        if ('마법의 소라고둥' in message.text) or ('마법의 소라고동' in message.text):
            bot.reply_to(message, BotFunctions.magic_conch(self))

        for n in range(len(resources.koreanFWord)):
            if resources.koreanFWord[n] in message.text:
                bot.reply_to(message, BotFunctions.fwordCTup(self))
