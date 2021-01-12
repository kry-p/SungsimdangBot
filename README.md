# 성심당봇

텔레그램 이용자에게 편의기능을 제공하기 위한 봇, 성심당봇입니다.   
이 봇은 성심당과는 관계가 없습니다.

## 실행 전 요구사항   
   
성심당봇은 ```Python 3``` 기반으로 작동하며 아래 라이브러리를 필요로 합니다.   
+ pyTelegramBotAPI
+ PhantomJS
+ beautifulsoup4
+ selenium
+ urllib3

또, 사용하고 있는 API는 아래와 같습니다.   
+ Telegram Bot API   
https://core.telegram.org/bots
+ Kakaomap REST API (좌표로 주소 변환하기)   
https://developers.kakao.com/docs/latest/ko/local/dev-guide#coord-to-address
+ OpenWeatherMap API (Current weather data)   
https://openweathermap.org/current

## 실행 방법

실행 전 요구사항에 작성된 라이브러리를 설치한 Python 환경이 필요합니다.   
가상 환경에서도 제한 없이 실행 가능하며, Raspberry Pi와 같은 환경에서 실행할 경우 Python 버전을 꼭 확인해 주세요.

실행하기에 앞서, 아래의
[사용자 정보 기입 방법](https://github.com/kry-p/SungsimdangBot#%EC%82%AC%EC%9A%A9%EC%9E%90-%EC%A0%95%EB%B3%B4-%EA%B8%B0%EC%9E%85-%EB%B0%A9%EB%B2%95)과 
[봇 설정 방법](https://github.com/kry-p/SungsimdangBot#%EB%B4%87-%EC%84%A4%EC%A0%95-%EB%B0%A9%EB%B2%95)을 참고하여 각각 수정해 주세요.   
특히 텔레그램 봇 토큰이 기입되지 않았을 경우 정상적으로 실행되지 않습니다.

실행 환경이 마련되면 ```/bin/main.py``` 파일을 실행하기만 하면 됩니다. 참 쉽죠?

## 기능 목록   
   
모든 기능은 그룹에서도 사용 가능하나, 봇에게 그룹 입장과 메시지 접근 권한을 부여하셔야 합니다.   
해당 권한은 텔레그램 ```@BotFather``` 를 통해 수정할 수 있으며, 자세한 내용은 https://core.telegram.org/bots 을 참조해 주세요.

1. 🌡 한강 수온 알림     
봇에게 ```🌊 수온```이나 ```😱 자살```이 포함된 메시지를 보낼 경우 실시간수질정보시스템으로부터 제공된 최근 수온 정보를 제공합니다.   
아래의 사용자 정보 기입 을 참고하여 사용자 정보를 저장해 두면 사용자별 수온 정보를 반환할 수 있습니다.

2. ✅ 선택봇     
```/pick``` 명령어와 함께 단어의 집합을 띄어쓰기로 구분하여 입력하면 그 중 하나를 선택하여 반환합니다.  
설정할 수 있는 추가 옵션은 없습니다.

3. 🔫 러시안 룰렛 게임     
러시안 룰렛 게임입니다. ```/roulette``` 명령어로 장전, ```/shoot``` 명령어로 격발, ```/flush_bullet``` 명령어로 약실을 비웁니다.

4. 🪙 동전뒤집기     
```/coin_toss``` 명령어를 입력하면 동전을 뒤집은 결과를 제공합니다.   
결과는 앞면과 뒷면입니다.

5. 🤬 나쁜말 감지기   
설정된 시간 제한 이내에 다수의 나쁜말이 감지된 경우 자제할 것을 촉구하는 메시지를 보냅니다.   
차후 감지기를 고도화할 예정에 있습니다.

6. 📍 현재 위치 정보   
텔레그램의 위치 기능을 사용하여 현재 위치를 메시지로 보낸 경우 그 상세 정보를 메시지로 보냅니다.   
제공하는 정보는 주소, 경위도, 날씨입니다.


## 사용자 정보 기입 방법

```resources.py``` 파일을 열면 아래와 같은 내용이 있습니다.   
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
http://www.koreawqi.go.kr/index_web.jsp 에서 사용자와 가깝거나 찾고자 하는 측정소 이름을 찾으시면 됩니다.

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

```bot_settings.py``` 파일을 열면 아래와 같은 내용이 있습니다.   
API 토큰을 제외하면 수정하지 않아도 사용에 오류가 발생하는 등의 지장은 없으니 필요에 따라 수정해 주세요.

```
# PLEASE be careful about handling API Keys!

# Telegram bot token
BOT_TOKEN = 'your telegram bot token'
# Kakaomap REST API token
MAP_TOKEN = 'your kakaomap rest api token'
# OpenWeatherMap API token
WEATHER_TOKEN = 'your openweathermap api token'

# Settings

# Bad word detector

DETECTOR_TIMEOUT = 600  # Time to detect from the first word sent
RECOGNIZER_COUNT = 10  # Number to detect (sending a message if exceeded this value)
```
⭐️ 표시는 필수입니다.   

+ BOT_TOKEN ⭐️   
텔레그램 봇 API 토큰입니다.   

+ MAP_TOKEN   
카카오맵 REST API 토큰입니다. 현재 위치 관련 정보를 제공받으려면 필요합니다.

+ WEATHER_TOKEN   
OpenWeatherMap API 토큰입니다. 현재 위치 관련 정보를 제공받으려면 필요합니다.

+ DETECTOR_TIMEOUT ⭐️   
나쁜말 감지기의 초 단위 시간제한입니다. 첫 번째 감지 이후 이 시간이 지나면 카운트가 초기화됩니다.

+ RECOGNIZER_COUNT ⭐️   
나쁜말 감지기의 감지 횟수입니다. 이 횟수를 넘으면 ```나쁜말 그만해``` 등과 같은 메시지를 보냅니다.


## 구현 예정인 기능
   
1. 추천, 비추천 글 정보   
🚧 작업 예정입니다. 🚧

2. 밈 반응기   
🚧 작업 예정입니다. 🚧
