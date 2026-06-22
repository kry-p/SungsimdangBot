import os

from dotenv import load_dotenv

# PLEASE be careful about handling API Keys!
load_dotenv()


def _int_env(key, default):
    value = os.getenv(key, "")
    return int(value) if value else default


def _int_env_with_fallback(primary: str, fallback_key: str, default: int) -> int:
    v = os.getenv(primary)
    if v is not None:
        return int(v)
    return _int_env(fallback_key, default)


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

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"

# AI 공통 (AI_* 우선, 없으면 GEMINI_* fallback)
AI_SESSION_TIMEOUT = _int_env_with_fallback("AI_SESSION_TIMEOUT", "GEMINI_SESSION_TIMEOUT", 3600)
AI_MAX_HISTORY = _int_env_with_fallback("AI_MAX_HISTORY", "GEMINI_MAX_HISTORY", 20)
AI_RATE_LIMIT = _int_env_with_fallback("AI_RATE_LIMIT", "GEMINI_RATE_LIMIT", 5)
AI_API_TIMEOUT = _int_env_with_fallback("AI_API_TIMEOUT", "GEMINI_API_TIMEOUT", 60)

ADMIN_USER_ID = _int_env("ADMIN_USER_ID", 0)

# RSS feed translator API
RSSF_TOKEN = os.getenv("RSSF_TOKEN", "")
RSSF_URL = os.getenv("RSSF_URL", "")

# External endpoints
NAMUWIKI_BASE_URL = "https://namu.wiki/w/"
SEARCH_BASE_URL = "https://dapi.kakao.com/v2/search/web?"
# NOTE: 서울 열린데이터 API는 HTTPS를 지원하지 않음 (2026-03-23 확인)
SEOUL_HANGANG_WATER_URL = f"http://openapi.seoul.go.kr:8088/{SEOUL_HANGANG_WATER_TOKEN}/json/WPOSInformationTime/1/5/"

REQUIRED_VARS = {"BOT_TOKEN": BOT_TOKEN}


def validate():
    missing = [name for name, value in REQUIRED_VARS.items() if not value]
    if missing:
        raise RuntimeError(f"Required environment variables not set: {', '.join(missing)}")
