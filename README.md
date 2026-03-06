# 성심당봇

<p>
    <img src="https://img.shields.io/badge/Python%203.x-%233776AB?style=flat-square&logo=python&logoColor=white"/>&nbsp
    <img src="https://img.shields.io/badge/Telegram%20Bot-%2326A5E4?style=flat-square&logo=telegram&logoColor=white"/>&nbsp
</p>

텔레그램 이용자에게 편의기능을 제공하기 위한 봇, 성심당봇입니다.<br>
이 봇은 성심당과는 관계가 없습니다.

## 요구사항

성심당봇은 `Python 3` 기반으로 작동하며 아래 라이브러리를 필요로 합니다.

+ pyTelegramBotAPI
+ requests
+ python-dotenv

사용하고 있는 API는 아래와 같습니다.

+ Telegram Bot API<br>
  https://core.telegram.org/bots
+ Kakao REST API (좌표로 주소 변환하기, 검색)<br>
  https://developers.kakao.com/docs
+ OpenWeatherMap API (Current weather data)<br>
  https://openweathermap.org/current
+ 서울 열린데이터 광장 - 서울시 한강 및 주요지천 수질 측정 자료<br>
  https://data.seoul.go.kr/dataList/OA-15488/S/1/datasetView.do

## 프로젝트 구조

```
bin/
  main.py              # 엔트리포인트 (봇 폴링, 메시지 핸들러)
config/
  config.py            # 환경변수 기반 설정 (API 토큰, 외부 URL 등)
modules/
  features_hub.py      # 핵심 기능 허브 (수온, 날씨, D-day, 계산기, 나쁜말 감지기)
  web_based.py         # 웹 기반 기능 (수온 조회, 검색)
  random_based.py      # 랜덤 기반 기능 (선택봇, 동전뒤집기, 러시안 룰렛)
  calculator.py        # 수식 계산기
  log.py               # 로깅 모듈
resources/
  strings.py           # 봇 메시지 문자열 상수
  users.py             # 사용자 정보 설정
```

## 실행 방법

### 1. 라이브러리 설치

```bash
pip install pyTelegramBotAPI requests python-dotenv
```

### 2. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 입력합니다.

```env
BOT_TOKEN=your_telegram_bot_token
KAKAO_TOKEN=your_kakao_rest_api_token
WEATHER_TOKEN=your_openweathermap_api_token
SEOUL_HANGANG_WATER_TOKEN=your_seoul_open_api_token
DETECTOR_TIMEOUT=600
DETECTOR_COUNT=10
```

### 3. 사용자 정보 설정 (선택)

아래의 [사용자 정보 기입 방법](#사용자-정보-기입-방법)을 참고하여 `resources/users.py`를 수정합니다.<br>
기입하지 않아도 사용에 지장은 없습니다.

### 4. 실행

```bash
python bin/main.py
```

가상 환경에서도 제한 없이 실행 가능하며, Raspberry Pi와 같은 환경에서 실행할 경우 Python 버전을 꼭 확인해 주세요.

## 기능 목록

모든 기능은 그룹에서도 사용 가능하나, 봇에게 그룹 입장과 메시지 접근 권한을 부여하셔야 합니다.<br>
해당 권한은 텔레그램 `@BotFather` 를 통해 수정할 수 있으며, 자세한 내용은 https://core.telegram.org/bots 을 참조해 주세요.

+ 🌡 한강 수온 알림<br>
   `수온`이나 `자살`이 포함된 메시지를 보낼 경우 서울 열린데이터 광장 API를 통해 현재 한강 수온 정보를 제공합니다.<br>
   예) `자살마렵다` → `현재 한강 수온은 2.7도입니다.`

+ ✅ 선택봇<br>
   `/pick` 명령어와 함께 단어의 집합을 띄어쓰기로 구분하여 입력하면 그 중 하나를 선택하여 반환합니다.<br>
   예) `/pick 퇴근할수있어 vs 퇴근못해` → `vs`

+ 🔫 러시안 룰렛 게임<br>
   러시안 룰렛 게임입니다. `/roulette` 명령어로 장전, `/shoot` 명령어로 격발, `/flush_bullet` 명령어로 약실을 비웁니다.<br>
   예) `/roulette 6 1` → `6발이 장전되었습니다.`

+ 🪙 동전뒤집기<br>
   `/coin_toss` 명령어를 입력하면 동전을 뒤집은 결과를 제공합니다.<br>
   결과는 앞면과 뒷면입니다.<br>
   예) `/coin_toss` → `동전뒤집기 결과 : 앞면`

+ 🤬 나쁜말 감지기<br>
   설정된 시간 제한 이내에 다수의 나쁜말이 감지된 경우 자제할 것을 촉구하는 메시지를 보냅니다.

+ 📍 현재 위치 정보<br>
   텔레그램의 위치 기능을 사용하여 현재 위치를 메시지로 보낸 경우 그 상세 정보를 메시지로 보냅니다.<br>
   제공하는 정보는 주소, 경위도, 날씨입니다.

+ 📅 D-day<br>
   `/dday`와 계산하고자 하는 날짜를 함께 입력하면 며칠 남았는지 또는 며칠 지났는지를 알려 드립니다.<br>
   예) `/dday 2020 12 31` → `12일 지났습니다.`

+ 🧮 계산기<br>
   수식을 입력하면 해당 수식의 결과를 반환합니다.<br>
   예) `/calc sin ( pi / 2 )` → `1.0`

+ 🔎 검색 (Beta)<br>
   검색어에 대한 결과를 링크와 함께 마크다운으로 반환합니다.<br>
   예) `/search 집가고싶다` → `(검색 결과)`

+ 🐚 마법의 소라고동<br>
   `마법의 소라고둥` 또는 `마법의 소라고동`이 포함된 메시지를 보내면 마법의 소라고동이 답변합니다.

## 사용자 정보 기입 방법

`resources/users.py` 파일을 열면 아래와 같은 내용이 있습니다.<br>
일부 특수 기능 사용을 위해 필요하며, 기입하지 않아도 사용에 오류가 발생하는 등의 지장은 없습니다.

```python
# User information
# ex) ['user_id', 'user_name', 'river_measure', 'river_alias', 'meme_list']
# 예) ['사용자 ID', '사용자명', '강물 온도 측정소 이름', '표시될 강 이름', '밈 반응기 밈 목록']
user = [['user_id', 'user_name', 'river_measure', 'river_alias', 'meme_list']]
```

각 필드의 설명은 아래와 같습니다. (⭐️ 표시는 필수)

+ user_id ⭐️<br>
  각 사용자의 고유한 ID이며, 사용자 식별을 위해 사용됩니다.<br>
  사용자 ID를 확인하는 방법은 차후 제공 예정입니다.

+ user_name<br>
  사용자 이름입니다.<br>
  각 사용자 ID에 대응하고자 하는 이름(또는 별명)을 입력합니다.

+ river_measure<br>
  실시간수질정보시스템이 제공하는 측정소 이름입니다.

+ river_alias<br>
  측정소 이름에 대응하는 강 이름(별명)입니다.<br>
  실제 결과 메시지에 표시하고자 하는 강 이름을 입력하시면 됩니다.

+ meme_list<br>
  🚧 밈 반응기의 밈 목록으로, 기능이 완성되면 작성 방법을 안내합니다. 🚧<br>
  🚧 그 전에는 `None`으로 두고 사용하시면 됩니다. 🚧

아래는 작성 예시입니다.

```python
user = [['1234567', '치코리타', '구리', '한강', None],
        ['7654321', '앨리스', '상동', '낙동강', None]]
```

## 환경변수

프로젝트 루트의 `.env` 파일에 아래 환경변수를 설정합니다. (⭐️ 표시는 필수)

| 변수명 | 필수 | 설명 |
|--------|------|------|
| `BOT_TOKEN` | ⭐️ | 텔레그램 봇 API 토큰 |
| `KAKAO_TOKEN` | | 카카오 REST API 토큰 (위치 정보, 검색 기능) |
| `WEATHER_TOKEN` | | OpenWeatherMap API 토큰 (위치 기반 날씨 정보) |
| `SEOUL_HANGANG_WATER_TOKEN` | | 서울 열린데이터 광장 API 토큰 (한강 수온 정보) |
| `DETECTOR_TIMEOUT` | | 나쁜말 감지기 시간제한 (초 단위, 기본값 600) |
| `DETECTOR_COUNT` | | 나쁜말 감지기 감지 횟수 (기본값 10) |

## 구현 예정인 기능

1. 추천, 비추천 글 정보<br>
   🚧 작업 예정입니다. 🚧

2. 밈 반응기<br>
   🚧 작업 예정입니다. 🚧

## 기여자

+ [@h1ghg3n](https://github.com/h1ghg3n) - 공동 개발

## FAQ

+ Q. 봇은 어떻게 만드나요?<br>
  먼저 텔레그램 계정이 있어야 합니다. [링크](https://t.me/BotFather)를 클릭하여 해당 봇의 지도를 따르면 됩니다.<br>
  아이디가 `@BotFather` 가 아닌 모든 계정은 사칭이니 주의하세요.

## 알려진 문제점

+ 하나의 봇 세션을 여러 그룹에서 함께 운용할 때 러시안 룰렛의 상태가 공유됨
+ 검색 결과를 마크다운으로 출력 시 괄호가 포함된 텍스트가 검색 결과에 포함되면 형식 오류 발생
