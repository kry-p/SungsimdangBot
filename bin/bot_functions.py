# Bot functions script

import random
import sqlite3
import resources
import bot_settings
import time
import datetime
import json
import requests
import urllib.parse

from selenium import webdriver
from bs4 import BeautifulSoup

TEMPERATURE_BASE_URL = 'http://www.koreawqi.go.kr/index_web.jsp'
MAP_BASE_URL = 'https://dapi.kakao.com/v2/local/geo/coord2address.json?'
WEATHER_BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'
DATA = './common_data.db'

userDB = sqlite3.connect(DATA)
cursor = userDB.cursor()


class UserManager:
    # init
    def __init__(self):
        pass


# 강물 온도 조회
class RiverTempManager:
    # init
    def __init__(self, driver):
        self.driver = driver
        self.suon = list()
        self.site = list()
        self.suon_temp = None
        self.site_temp = None
        self.html = None
        self.soup = None
        # Records current time and latest update 현재 시간과 마지막 업데이트 시점을 기록
        self.currentTime = datetime.datetime.now()
        self.lastUpdateTime = datetime.datetime(self.currentTime.year,
                                                self.currentTime.month,
                                                self.currentTime.day,
                                                self.currentTime.hour,
                                                1)
        if self.currentTime.minute == 0:
            self.lastUpdateTime -= datetime.timedelta(hours=1)

        # Initialize current temperature information 현재 온도 정보를 최초 설정
        self.update()

    # Update current temperature data 현재 온도 정보를 업데이트
    def update(self):
        # check recently update temperature info 최근에 업데이트하였는지 확인
        self.currentTime = datetime.datetime.now()
        interval = (self.currentTime - self.lastUpdateTime).seconds

        if self.suon and interval < 3600:
            return
        else:
            self.driver.get(TEMPERATURE_BASE_URL)
            self.driver.switch_to.frame('MainFrame')
            self.html = self.driver.page_source
            self.soup = BeautifulSoup(self.html, 'html.parser')

            self.site_temp = self.soup.select("tr[class^='site'] > th")
            self.suon_temp = self.soup.select('tr > td.avg1')

            for i in self.site_temp:
                self.site.append(i.text.strip())
            for i in self.suon_temp:
                self.suon.append(i.text.strip())

    # Provide temperature data to other methods 다른 메소드로 온도 정보 전달
    def provide(self, site):
        try:
            position = self.site.index(site)
            return self.suon[position]
        except ValueError:
            return 'error'


class GaechuInfo:
    # init
    def __init__(self):
        pass


class BotFunctions:
    # init
    def __init__(self, bot):
        BotFunctions.driver = webdriver.PhantomJS()
        self.badWordCount = 0  # 나쁜 말 카운트
        self.firstBadWordTimestamp = 0  # 나쁜 말 감지기가 최초 활성화된 시점
        self.Bullet = ()
        self.bot = bot

        self.riverTempManager = RiverTempManager(BotFunctions.driver)

    # Get current river temperature 현재 강물 온도 정보 획득
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
        # Default : Hangang(Guri) 잘못된 값이 입력된 경우 기본값으로 한강 구리 측정소 정보를 반환
        try:
            if result == 'error':
                return '현재 한강 수온은 ' + self.riverTempManager.provide('구리') + '도입니다.'
            else:
                return '현재 ' + alias + ' 수온은 ' + self.riverTempManager.provide(site) + '도입니다.'
        except AttributeError:
            return '현재 한강 수온은 ' + self.riverTempManager.provide('구리') + '도입니다.'

    # Random picker 랜덤픽
    def picker(self, msg):
        random.seed()
        split = msg.split()
        split = [item for item in split if '/pick' not in item]

        try:
            choice = random.choice(split)
        except IndexError:
            return resources.pickerErrorMsg

        return choice

    # Coin toss-up 동전뒤집기
    def coin_toss(self):
        random.seed()
        return '동전뒤집기 결과 : ' + random.choice(resources.coinTossResult)

    # Spongebob SquarePants magic conch 마법의 소라고동
    def magic_conch(self):
        random.seed()
        init_rand = random.randrange(0, 3)
        return resources.magicConchSentence[init_rand][
            random.randrange(0, len(resources.magicConchSentence[init_rand]))]

    # Russian roulette 러시안 룰렛
    def russian_roulette(self, msg):
        try:
            if msg.split()[1].isdigit() and msg.split()[2].isdigit():
                if msg.split()[1] == 0 and msg.split()[2] == 0:
                    self.Bullet = ()
                    return "약실을 비웠습니다. 사용하려면 다시 장전해주세요."
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

    # Launch roulette 러시안 룰렛 격발
    def trig_bullet(self):
        if len(self.Bullet) == 0:
            return resources.shotErrorMsg
        check = self.Bullet.pop()
        if check:
            return resources.shotRealMsg
        else:
            return resources.shotBlindMsg

    # Bad word detector 나쁜말 감지기
    def bad_word_detector(self, message, word_type):
        if not self.firstBadWordTimestamp:
            self.firstBadWordTimestamp = time.time()
        self.badWordCount += 1

        if ((time.time() - self.firstBadWordTimestamp) <= bot_settings.DETECTOR_TIMEOUT) \
                and self.badWordCount >= bot_settings.RECOGNIZER_COUNT:
            if word_type == 'f_word':
                self.bot.send_message(message.chat.id, random.choice(resources.stopFWord))
            elif word_type == 'anitiation':
                self.bot.send_message(message.chat.id, random.choice(resources.stopAnitiation))
        elif ((time.time() - self.firstBadWordTimestamp) >= bot_settings.DETECTOR_TIMEOUT) \
                and self.badWordCount <= bot_settings.RECOGNIZER_COUNT:
            self.firstBadWordTimestamp = 0
            self.badWordCount = 0

    # D-day
    def d_day(self, message):
        now = datetime.datetime.now()  # today
        today = datetime.date(now.year,
                              now.month,
                              now.day)

        split = message.text.split()
        split = [item for item in split if '/dday' not in item]
        split = list(map(int, split))  # String to calculable integer values

        try:
            dest = datetime.date(split[0], split[1], split[2])  # date that user entered

            result = (dest - today).days

            if result == 0:
                self.bot.reply_to(message, resources.dayDestMsg)
            elif result > 0:
                self.bot.reply_to(message, str(result) + resources.dayLeftMsg)
            elif result < 0:
                self.bot.reply_to(message, str(-1 * result) + resources.dayPassedMsg)

        except (ValueError and IndexError):  # wrong input
            self.bot.reply_to(message, resources.dayOutOfRangeMsg)

    # Geolocation information　위치 기반 정보 제공
    def geolocation_info(self, message, latitude, longitude):

        # location info
        map_args = {'x': longitude, 'y': latitude}
        map_url = MAP_BASE_URL + urllib.parse.urlencode(map_args)
        map_headers = {"Authorization": 'KakaoAK ' + bot_settings.MAP_TOKEN}
        map_request = requests.get(map_url, headers=map_headers)

        # weather info (by OpenWeatherMap)
        weather_args = {'lang': 'kr', 'appid': bot_settings.WEATHER_TOKEN, 'lat': latitude, 'lon': longitude}
        weather_url = WEATHER_BASE_URL + urllib.parse.urlencode(weather_args)
        weather_request = requests.get(weather_url)
        weather_json = json.loads(weather_request.text)

        # temporarily store weather info
        weather = weather_json['weather'][0]['description']
        temp = str(round(weather_json['main']['temp'] - 273.15)) + '°C'
        feels_temp = str(round(weather_json['main']['feels_like'] - 273.15)) + '°C'
        humidity = str(round(weather_json['main']['humidity'])) + '%'

        # makes script and sends message
        weather_result = '날씨 ' + weather + ', ' + '기온 ' + temp + ', ' + \
                         '체감온도 ' + feels_temp + ', ' + '습도 ' + humidity

        maplocation = json.loads(map_request.text)['documents'][0]['address']['address_name']
        geolocation = "위도 : " + str(latitude) + ", 경도 : " + str(longitude)

        result = geolocation + '\n' + maplocation + '\n\n' + weather_result

        self.bot.reply_to(message, result)

    # Handling ordinary message 일반 메시지 처리
    def ordinary_message(self, chat_id, message):
        print(message)

        # Bad word detector 나쁜말 감지기
        for n in range(len(resources.koreanFWord)):
            if resources.koreanFWord[n] in message.text:
                BotFunctions.bad_word_detector(self, message, 'f_word')

        # 아니시에이션 감지기
        for n in range(len(resources.anitiationWord)):
            if resources.anitiationWord[n] in message.text:
                BotFunctions.bad_word_detector(self, message, 'anitiation')

        # location-based message if user sent message that includes '수온' or '자살'
        if ('수온' in message.text) or ('자살' in message.text):
            self.bot.reply_to(message, BotFunctions.get_temp(self, message.from_user.id))

        # randomly select magic conch message if user sent message that includes '마법의 소라고둥/동'
        if ('마법의 소라고둥' in message.text) or ('마법의 소라고동' in message.text):
            self.bot.reply_to(message, BotFunctions.magic_conch(self))
