# Bot functions script

import random
import sqlite3
import resources
import time

from selenium import webdriver
from bs4 import BeautifulSoup

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
        self.suon = list()
        self.site = list()
        self.suon_temp = None
        self.site_temp = None

        self.html = None
        self.soup = None
        self.driver = driver
        # 클래스 생성 시각이 1시 37분이라면 1시+ 1분(서버와의 딜레이)이 기록됨.
        self.tempCtime = int(time.time()) - \
                            (int(time.time()) % 3600) + 60
        # 이 시점의 업데이트는 기록이 없는 상태라 새로 생성된 갱신시각이 업데이트되지 않은채로 리스트와 수온만 받아옴.
        self.update()

    # Update current temperature data
    def update(self):
        # check recently update temperature info
        if not self.suon and int(time.time()) - self.tempCtime < 3600 \
                or int(time.time()) - self.tempCtime >= 3600:  # 갱신 시각 1시간 이전, 리스트 존재시, 갱신시각 한시간 이후
            self.driver.get(TEMPERATURE_URL)
            self.driver.switch_to.frame('MainFrame')
            self.html = self.driver.page_source
            self.soup = BeautifulSoup(self.html, 'html.parser')

            self.site_temp = self.soup.select("tr[class^='site'] > th")
            self.suon_temp = self.soup.select('tr > td.avg1')

            for i in self.site_temp:
                self.site.append(i.text.strip())
            for i in self.suon_temp:
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
        self.fwordCount = 0
        self.startFtime = 0
        self.Bullet = ()

        self.riverTempManager = RiverTempManager(BotFunctions.driver)

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
                return '현재 한강 수온은 ' + self.riverTempManager.provide('구리') + '도입니다.'
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

    def russian_roulette(self, msg):
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
            return resources.rouletteErrorMsg

    def trig_bullet(self):
        if len(self.Bullet) == 0:
            return resources.shotErrorMsg
        check = self.Bullet.pop()
        if check:
            return resources.shotRealMsg
        else:
            return resources.shotBlindMsg

    def fword_recognizer(self, bot, message):
        if not self.startFtime:
            self.startFtime = time.time()
        self.fwordCount += 1

        if ((time.time() - self.startFtime) <= 600) and self.fwordCount >= 10:
            bot.send_message(message.chat.id, '다들 진정해')
        elif ((time.time() - self.startFtime) >= 600) and self.fwordCount <= 10:
            self.startFtime = 0
            self.fwordCount = 0

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
                BotFunctions.fword_recognizer(self, bot, message)
