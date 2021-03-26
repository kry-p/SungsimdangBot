# Bot features script

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import datetime
import json
import random
import time
import urllib.parse
import requests

from config import config
from modules.calculator import Calculator
from modules.ramdom_based import RandomBasedFeatures
from modules.river_temp import RiverTempManager
from resources import strings
from resources import users
from multiprocessing import Process

MAP_BASE_URL = 'https://dapi.kakao.com/v2/local/geo/coord2address.json?'
WEATHER_BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'


class BotFeaturesHub:
    # init
    def __init__(self, bot):
        self.badWordCount = 0  # 나쁜 말 카운트
        self.firstBadWordTimestamp = 0  # 나쁜 말 감지기가 최초 활성화된 시점
        self.bot = bot
        self.mtChatList = {}

        self.randomBasedFeatures = RandomBasedFeatures()
        self.riverTempManager = RiverTempManager()
        self.calculator = Calculator()

    # Get current river temperature 현재 강물 온도 정보 획득
    def get_temp(self, user_id):
        site = ''
        alias = ''
        self.riverTempManager.update()

        try:
            for user in users.user:
                if user[0] == str(user_id):
                    site = user[2]
                    alias = user[3]
        except IndexError:
            pass

        result = self.riverTempManager.provide(site)
        result_if_error = self.riverTempManager.provide('구리')
        # Default : Hangang(Guri) 잘못된 값이 입력된 경우 기본값으로 한강 구리 측정소 정보를 반환
        try:
            if result == 'error':
                if result_if_error == 'error':
                    return '현재 한강 수온 정보를 가져올 수 없습니다.'
                else:
                    return '현재 한강 수온은 ' + self.riverTempManager.provide('구리') + '도입니다.'
            else:
                return '현재 ' + alias + ' 수온은 ' + self.riverTempManager.provide(site) + '도입니다.'
        except AttributeError:
            if result == 'error':
                if result_if_error == 'error':
                    return '현재 한강 수온 정보를 가져올 수 없습니다.'
                else:
                    return '현재 한강 수온은 ' + self.riverTempManager.provide('구리') + '도입니다.'

    # Bad word detector 나쁜말 감지기
    def bad_word_detector(self, message, word_type):
        if not self.firstBadWordTimestamp:
            self.firstBadWordTimestamp = time.time()
        self.badWordCount += 1

        if ((time.time() - self.firstBadWordTimestamp) <= config.DETECTOR_TIMEOUT) \
                and self.badWordCount >= config.DETECTOR_COUNT:
            if word_type == 'f_word':
                self.bot.send_message(message.chat.id, random.choice(strings.stopFWord))
            elif word_type == 'anitiation':
                self.bot.send_message(message.chat.id, random.choice(strings.stopAnitiation))
        elif ((time.time() - self.firstBadWordTimestamp) >= config.DETECTOR_TIMEOUT) \
                and self.badWordCount <= config.DETECTOR_COUNT:
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
                self.bot.reply_to(message, strings.dayDestMsg)
            elif result > 0:
                self.bot.reply_to(message, str(result) + strings.dayLeftMsg)
            elif result < 0:
                self.bot.reply_to(message, str(-1 * result) + strings.dayPassedMsg)

        except (ValueError and IndexError):  # wrong input
            self.bot.reply_to(message, strings.dayOutOfRangeMsg)

    # mute 봇이 시끄러운 사람들을 위한 조치
    def mute_by_friedsoboru(self, message):
        stdtime = time.time()
        settime = message.split()[1:]
        idfchat = 'CH_' + message.chat.id

        if len(settime) < 1 or len(settime) > 2:
            self.bot.reply_to(message, strings.muteErrorMsg)
            return
        elif len(settime) == 1 and not settime[0].isdigit:
            self.bot.reply_to(message, strings.muteErrorMsg)
            return
        elif (not len(settime)) == 2 or (not settime[1].isdigit):
            if not(settime[0].isdigit or settime[1].isdigit):
                self.bot.reply_to(message, strings.muteErrorMsg)
                return

        if len(settime) == 1:
            if settime[0] > 60 or settime[0] < 0 :
                self.bot.reply_to(message, strings.muteOORMsg)
                return
        elif len(settime) == 2:
            if (settime[0]*60+settime[1]) < 0 or (settime[0]*60+settime[1]) > 3600:
                self.bot.reply_to(message, strings.muteOORMsg)
                return

        self.mtChatList[idfchat] = stdtime + settime[0] * 60 + settime[1]
        self.bot.reply_to(message, strings.muteSuccessMsg.format(settime[0], settime[1]))

    def sbrchecker(self, chat_id):  # 봇에게 정당한 휴식의 권리를, 아직 다 안먹었냐 물어보기
        if self.mtChatList['CH_' + chat_id] - time.time() > 0:  # 시간이 아직 안되었으면
            return True
        else:
            return False

    # Geolocation information　위치 기반 정보 제공
    def geolocation_info(self, message, latitude, longitude):

        # location info
        map_args = {'x': longitude, 'y': latitude}
        map_url = MAP_BASE_URL + urllib.parse.urlencode(map_args)
        map_headers = {"Authorization": 'KakaoAK ' + config.MAP_TOKEN}
        map_request = requests.get(map_url, headers=map_headers)

        # weather info (by OpenWeatherMap)
        weather_args = {'lang': 'kr', 'appid': config.WEATHER_TOKEN, 'lat': latitude, 'lon': longitude}
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

        map_location = json.loads(map_request.text)['documents'][0]['address']['address_name']
        geo_location = "위도 : " + str(latitude) + ", 경도 : " + str(longitude)

        result = geo_location + '\n' + map_location + '\n\n' + weather_result

        self.bot.reply_to(message, result)

    def calculator_handler(self, message):
        if self.sbrchecker(message.chat_id):
            pass
        elif self.calculator.wrong_syntax_checker(message.text) != 'syntax error':
            result = self.calculator.operation(message.text)

            if result == 'syntax error':
                self.bot.reply_to(message, strings.calcSyntaxErrorMsg)
            elif result == 'division by zero error':
                self.bot.reply_to(message, strings.calcDivisionByZeroErrorMsg)
            elif result == 'pass':
                pass
            else:
                self.bot.reply_to(message, result)

    # Handling ordinary message 일반 메시지 처리
    def ordinary_message(self, chat_id, message):
        if self.sbrchecker(chat_id):
            return
        print(message)

        # simplified calculator 간단 계산기
        self.calculator_handler(message)

        # Bad word detector 나쁜말 감지기
        for n in range(len(strings.koreanFWord)):
            if strings.koreanFWord[n] in message.text:
                self.bad_word_detector(message, 'f_word')

        # 아니시에이션 감지기
        for n in range(len(strings.anitiationWord)):
            if strings.anitiationWord[n] in message.text:
                self.bad_word_detector(message, 'anitiation')

        # location-based message if user sent message that includes '수온' or '자살'
        if ('수온' in message.text) or ('자살' in message.text):
            self.bot.reply_to(message, self.get_temp(message.from_user.id))

        # randomly select magic conch message if user sent message that includes '마법의 소라고둥/동'
        if ('마법의 소라고둥' in message.text) or ('마법의 소라고동' in message.text):
            self.bot.reply_to(message, self.randomBasedFeatures.magic_conch())
