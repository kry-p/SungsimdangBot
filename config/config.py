# PLEASE be careful about handling API Keys!

# Telegram bot token 텔레그램 봇 토큰
BOT_TOKEN = 'your token here'
# Kakao REST API token 카카오 REST API 토큰
KAKAO_TOKEN = 'your token here'
# OpenWeatherMap API token 오픈웨더맵 API 토큰
WEATHER_TOKEN = 'your token here'

# Settings 설정

# Global 전역 설정

CHROME_DRIVER_PATH = 'your path here'  # Chrome driver path (like '/usr/lib/chromium-browser/chromedriver')

# Bad word detector 나쁜말 감지기

DETECTOR_TIMEOUT = 600  # Time to detect from the first word sent 첫 단어로부터 감지할 시간(초 단위)
DETECTOR_COUNT = 10  # Number to detect (sending a message if exceeded this value) 감지할 개수 (이 횟수를 넘으면 메시지 전송)
