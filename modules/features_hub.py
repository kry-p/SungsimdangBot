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
from modules.random_based import RandomBasedFeatures
from modules.web_based import WebManager
from resources import strings
from resources import users

MAP_BASE_URL = 'https://dapi.kakao.com/v2/local/geo/coord2address.json?'
WEATHER_BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'


class BotFeaturesHub:
    # init
    def __init__(self, bot):
        self.badWordCount = 0  # 나쁜 말 카운트
        self.firstBadWordTimestamp = 0  # 나쁜 말 감지기가 최초 활성화된 시점
        self.bot = bot

        self.randomBasedFeatures = RandomBasedFeatures()
        self.webManager = WebManager()
        self.calculator = Calculator()

    # Get current river temperature 현재 강물 온도 정보 획득
    def get_temp(self, user_id):
        site = ''
        alias = ''
        self.webManager.update_suon()

        try:
            for user in users.user:
                if user[0] == str(user_id):
                    site = user[2]
                    alias = user[3]
        except IndexError:
            pass

        result = self.webManager.provide_suon(site)
        result_if_error = self.webManager.provide_suon('구리')
        # Default : Hangang(Guri) 잘못된 값이 입력된 경우 기본값으로 한강 구리 측정소 정보를 반환
        try:
            if result == 'error':
                if result_if_error == 'error':
                    return '현재 한강 수온 정보를 가져올 수 없습니다.'
                else:
                    return '현재 한강 수온은 ' + self.webManager.provide_suon('구리') + '도입니다.'
            else:
                return '현재 ' + alias + ' 수온은 ' + self.webManager.provide_suon(site) + '도입니다.'
        except AttributeError:
            if result == 'error':
                if result_if_error == 'error':
                    return '현재 한강 수온 정보를 가져올 수 없습니다.'
                else:
                    return '현재 한강 수온은 ' + self.webManager.provide_suon('구리') + '도입니다.'

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

    # Geolocation information　위치 기반 정보 제공
    def geolocation_info(self, message, latitude, longitude):

        # location info
        map_args = {'x': longitude, 'y': latitude}
        map_url = MAP_BASE_URL + urllib.parse.urlencode(map_args)
        map_headers = {"Authorization": 'KakaoAK ' + config.KAKAO_TOKEN}
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

    # Calculator 계산기
    def calculator_handler(self, message):
        # cut command string
        command = message.text.split()[0]

        if len(message.text.split()) >= 2:
            actual_text = message.text[len(command):]

            # calculate
            result = self.calculator.operation(actual_text)

            # error handling
            if result == 'syntax error':
                self.bot.reply_to(message, strings.calcSyntaxErrorMsg)
            elif result == 'division by zero error':
                self.bot.reply_to(message, strings.calcDivisionByZeroErrorMsg)
            else:
                self.bot.reply_to(message, result)

    # Handling ordinary message 일반 메시지 처리
    def ordinary_message(self, message):
        # print(message)

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
