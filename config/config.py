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
SEOUL_HANGANG_WATER_TOKEN = os.getenv("SEOUL_HANGANG_WATER_TOKEN", "")

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_SESSION_TIMEOUT = int(os.getenv("GEMINI_SESSION_TIMEOUT", "3600"))
GEMINI_MAX_HISTORY = int(os.getenv("GEMINI_MAX_HISTORY", "20"))
GEMINI_RATE_LIMIT = int(os.getenv("GEMINI_RATE_LIMIT", "5"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
GEMINI_ALLOWLIST_PATH = os.getenv("GEMINI_ALLOWLIST_PATH", "data/allowed_chats.json")

# External endpoints
NAMUWIKI_BASE_URL = "https://namu.wiki/w/"
SEARCH_BASE_URL = "https://dapi.kakao.com/v2/search/web?"
SEOUL_HANGANG_WATER_URL = f"http://openapi.seoul.go.kr:8088/{SEOUL_HANGANG_WATER_TOKEN}/json/WPOSInformationTime/1/5/"
