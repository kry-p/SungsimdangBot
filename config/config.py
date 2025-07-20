import os
from dotenv import load_dotenv
# PLEASE be careful about handling API Keys!
load_dotenv()

# Telegram bot token 텔레그램 봇 토큰
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Kakao REST API token 카카오 REST API 토큰
KAKAO_TOKEN = os.getenv("KAKAO_TOKEN")
# OpenWeatherMap API token 오픈웨더맵 API 토큰
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")
# Seoul Metropolitan City "서울시 한강 및 주요지천 수질 측정 자료" Open API token 
# 서울 열린데이터 광장 "서울시 한강 및 주요지천 수질 측정 자료" API 토큰
# see: https://data.seoul.go.kr/dataList/OA-15488/S/1/datasetView.do
SEOUL_HANGANG_WATER_TOKEN = os.getenv("SEOUL_HANGANG_WATER_TOKEN")

# Settings 설정

# Global 전역 설정
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")  # Chrome driver path (like '/usr/lib/chromium-browser/chromedriver')

# Bad word detector 나쁜말 감지기
DETECTOR_TIMEOUT = os.getenv("DETECTOR_TIMEOUT")  # Time to detect from the first word sent 첫 단어로부터 감지할 시간(초 단위)
DETECTOR_COUNT = os.getenv("DETECTOR_COUNT")  # Number to detect (sending a message if exceeded this value) 감지할 개수 (이 횟수를 넘으면 메시지 전송)

# External endpoints
TEMPERATURE_BASE_URL = 'http://water.nier.go.kr/'
NAMUWIKI_BASE_URL = 'https://namu.wiki/w/'
SEARCH_BASE_URL = 'https://dapi.kakao.com/v2/search/web?'
SEOUL_HANGANG_WATER_URL = f'http://openapi.seoul.go.kr:8088/{SEOUL_HANGANG_WATER_TOKEN}/json/WPOSInformationTime/1/5/'