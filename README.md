# 성심당봇

<p>
    <img src="https://img.shields.io/badge/backend-Python%203.x-%233776AB?style=flat-square&logo=python"/>&nbsp
    <img src="https://img.shields.io/badge/using-Selenium-%2343B02A?style=flat-square&logo=selenium"/>&nbsp 
</p>

텔레그램 이용자에게 편의기능을 제공하기 위한 봇, 성심당봇입니다.   
이 봇은 성심당과는 관계가 없습니다.

## 실행 전 요구사항

성심당봇은 ```Python 3``` 기반으로 작동하며 아래 라이브러리를 필요로 합니다.

+ pyTelegramBotAPI
+ beautifulsoup4
+ selenium
+ urllib3

또, 사용하고 있는 API는 아래와 같습니다.

+ Telegram Bot API   
  https://core.telegram.org/bots
+ Kakao REST API (좌표로 주소 변환하기, 검색)   
  https://developers.kakao.com/docs
+ OpenWeatherMap API (Current weather data)   
  https://openweathermap.org/current

이외에도 웹 리소스를 사용하기 위해 헤드리스 ChromeDriver를 사용하고 있습니다.

## 실행 방법

실행 전 요구사항에 작성된 라이브러리를 설치한 Python 환경과 ChromeDriver의 설치가 필요합니다.   
가상 환경에서도 제한 없이 실행 가능하며, Raspberry Pi와 같은 환경에서 실행할 경우 Python 버전을 꼭 확인해 주세요.

실행하기에 앞서, 아래의
[사용자 정보 기입 방법](https://github.com/kry-p/SungsimdangBot#%EC%82%AC%EC%9A%A9%EC%9E%90-%EC%A0%95%EB%B3%B4-%EA%B8%B0%EC%9E%85-%EB%B0%A9%EB%B2%95)과
[봇 설정 방법](https://github.com/kry-p/SungsimdangBot#%EB%B4%87-%EC%84%A4%EC%A0%95-%EB%B0%A9%EB%B2%95)을 참고하여 각각 수정해 주세요.   
특히 텔레그램 봇 토큰이 기입되지 않았을 경우 정상적으로 실행되지 않습니다.

위 작업을 수행하고  ```/bin/main.py``` 파일을 실행하면 봇이 가동됩니다.

## 기능 목록

모든 기능은 그룹에서도 사용 가능하나, 봇에게 그룹 입장과 메시지 접근 권한을 부여하셔야 합니다.   
해당 권한은 텔레그램 ```@BotFather``` 를 통해 수정할 수 있으며, 자세한 내용은 https://core.telegram.org/bots 을 참조해 주세요.

+ 🌡 가까운 강 수온 알림     
   봇에게 ```🌊 수온```이나 ```😱 자살```이 포함된 메시지를 보낼 경우 실시간수질정보시스템으로부터 제공된 최근 수온 정보를 제공합니다.   
   아래의 사용자 정보 기입 을 참고하여 사용자 정보를 저장해 두면 사용자별 수온 정보를 반환할 수 있습니다.   
   예) ```자살마렵다``` → ```현재 한강 수온은 2.7도입니다.```

+ ✅ 선택봇     
   ```/pick``` 명령어와 함께 단어의 집합을 띄어쓰기로 구분하여 입력하면 그 중 하나를 선택하여 반환합니다.   
   예) ```/pick 퇴근할수있어 vs 퇴근못해``` → ```vs```

+ 🔫 러시안 룰렛 게임     
   러시안 룰렛 게임입니다. ```/roulette``` 명령어로 장전, ```/shoot``` 명령어로 격발, ```/flush_bullet``` 명령어로 약실을 비웁니다.   
   예) ```/roulette 6 1 ``` → ```6발이 장전되었습니다.```
 
+ 🪙 동전뒤집기     
   ```/coin_toss``` 명령어를 입력하면 동전을 뒤집은 결과를 제공합니다.   
   결과는 앞면과 뒷면입니다.   
   예) ```/coin_toss``` → ```동전뒤집기 결과 : 앞면```
 
+ 🤬 나쁜말 감지기   
   설정된 시간 제한 이내에 다수의 나쁜말이 감지된 경우 자제할 것을 촉구하는 메시지를 보냅니다.   
   차후 감지기를 고도화할 예정에 있습니다.

+ 📍 현재 위치 정보   
   텔레그램의 위치 기능을 사용하여 현재 위치를 메시지로 보낸 경우 그 상세 정보를 메시지로 보냅니다.   
   제공하는 정보는 주소, 경위도, 날씨입니다.

+ 📅 D-day   
   ```/dday```와 계산하고자 하는 날짜를 함께 입력하면 며칠 남았는지 또는 며칠 지났는지를 알려 드립니다.   
   예) ```/dday 2020 12 31``` → ```12일 지났습니다.```

+ 🧮 계산기   
   수식을 입력하면 해당 수식의 결과를 반환합니다.  
   예) ```sin ( pi / 2 )``` → ```1.0```
   
+ 🔎 검색 (Beta)   
   검색어에 대한 결과를 링크와 함께 마크다운으로 반환합니다.  
   예) ```/search 집가고싶다``` → ```(검색 결과)```

## 사용자 정보 기입 방법

```/resources/users.py``` 파일을 열면 아래와 같은 내용이 있습니다.   
일부 특수 기능 사용을 위해 필요하며, 기입하지 않아도 사용에 오류가 발생하는 등의 지장은 없습니다.

```
# User information
# ex) ['user_id', 'user_name', 'river_measure', 'river_alias', 'meme_list']
# 예) ['사용자 ID', '사용자명', '강물 온도 측정소 이름', '표시될 강 이름', '밈 반응기 밈 목록']
user = [['user_id', 'user_name', 'river_measure', 'river_alias', 'meme_list']]
```

⭐️ 표시는 필수입니다.

+ user_id ⭐️   
  각 사용자의 고유한 ID이며, 사용자 식별을 위해 사용됩니다.   
  사용자 ID를 확인하는 방법은 차후 제공 예정입니다.

+ user_name   
  사용자 이름입니다.   
  각 사용자 ID에 대응하고자 하는 이름(또는 별명)을 입력합니다.

+ river_measure   
  실시간수질정보시스템이 제공하는 측정소 이름입니다.   
  http://water.nier.go.kr/ 에서 사용자와 가깝거나 찾고자 하는 측정소 이름을 찾으시면 됩니다.

+ river_alias   
  측정소 이름에 대응하는 강 이름(별명)입니다.   
  실제 결과 메시지에 표시하고자 하는 강 이름을 입력하시면 됩니다.

+ meme_list   
  🚧 밈 반응기의 밈 목록으로, 기능이 완성되면 작성 방법을 안내합니다. 🚧   
  🚧 그 전에는 ```None```으로 두고 사용하시면 됩니다. 🚧

아래는 작성 예시입니다.

```
user = [['1234567', '치코리타', '구리', '한강', None],
        ['7654321', '앨리스', '상동', '낙동강', None]]
```

## 봇 설정 방법

```/config/config.py``` 파일을 열면 아래와 같은 내용이 있습니다.   
API 토큰을 제외하면 수정하지 않아도 사용에 오류가 발생하는 등의 지장은 없으니 필요에 따라 수정해 주세요.

```
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
```

⭐️ 표시는 필수입니다.

+ BOT_TOKEN ⭐️   
  텔레그램 봇 API 토큰입니다.

+ KAKAO_TOKEN   
  카카오 REST API 토큰입니다. 현재 위치 관련 정보 및 검색 기능을 제공받으려면 필요합니다.

+ WEATHER_TOKEN   
  OpenWeatherMap API 토큰입니다. 현재 위치 관련 정보를 제공받으려면 필요합니다.

+ CHROME_DRIVER_PATH ⭐️  
  웹 페이지 처리를 위한 ChromeDriver 경로입니다. 드라이버 설치 후 경로를 입력해 주세요.

+ DETECTOR_TIMEOUT ⭐️   
  나쁜말 감지기의 초 단위 시간제한입니다. 첫 번째 감지 이후 이 시간이 지나면 카운트가 초기화됩니다.

+ DETECTOR_COUNT ⭐️   
  나쁜말 감지기의 감지 횟수입니다. 이 횟수를 넘으면 ```나쁜말 그만해``` 등과 같은 메시지를 보냅니다.

## 구현 예정인 기능

1. 추천, 비추천 글 정보   
   🚧 작업 예정입니다. 🚧

2. 밈 반응기   
   🚧 작업 예정입니다. 🚧

## 기여자

+ [@h1ghg3n](https://github.com/h1ghg3n) - 공동 개발

## FAQ

+ Q. 봇은 어떻게 만드나요?   
  먼저 텔레그램 계정이 있어야 합니다. [링크](https://t.me/BotFather)를 클릭하여 해당 봇의 지도를 따르면 됩니다.   
  아이디가 ```@BotFather``` 가 아닌 모든 계정은 사칭이니 주의하세요.

## 알려진 문제점

+ 하나의 봇 세션을 여러 그룹에서 함께 운용할 때 러시안 룰렛의 상태가 공유됨
+ 검색 결과를 마크다운으로 출력 시 괄호가 포함된 텍스트가 검색 결과에 포함되면 형식 오류 발생
