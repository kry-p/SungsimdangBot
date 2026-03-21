# 코드 컨벤션

## 네이밍 규칙

- **클래스**: PascalCase (`Calculator`, `BotFeaturesHub`, `WebManager`)
- **메서드/함수**: snake_case (`coin_toss`, `bad_word_detector`)
- **인스턴스 변수**: camelCase (레거시 컨벤션, 점진적으로 snake_case 전환 중) (`badWordCount`, `suonV2`)
- **상수**: UPPER_SNAKE_CASE (`BOT_TOKEN`, `DETECTOR_TIMEOUT`)
- **모듈 파일**: snake_case (`random_based.py`, `features_hub.py`)
- **언어**: 코드는 영문, 사용자 대상 메시지는 한국어

## import 패턴

- 각 디렉토리에 `__init__.py`가 있어 패키지로 인식됨
- `from modules.calculator import Calculator` 형태의 절대 import 사용
- 표준 라이브러리 → 서드파티 → 프로젝트 모듈 순서로 import

## 문자열 관리

- 모든 사용자 대상 메시지(한국어)는 `resources/strings.py`에 정의
- 모듈 코드에 사용자 대상 문자열을 하드코딩하지 않음 — `strings.xxx_msg` 참조
- 도움말 메시지 패턴: `strings.xxx_help_msg` / 에러 메시지 패턴: `strings.xxx_error_msg`

## 에러 처리

- 봇 기능은 raw exception 대신 한국어 에러 메시지를 반환
- 로깅은 `modules/log.py`의 Logger 클래스 사용

## 아키텍처 패턴

- **Hub 패턴**: `BotFeaturesHub`가 모든 기능 모듈의 인스턴스를 소유하고 위임
- **정적 메서드**: 상태 없는 기능 메서드(예: `picker`, `coin_toss`)는 `@staticmethod`
- **메시지 핸들러**: `bin/main.py`에서 `@bot.message_handler()` 데코레이터 사용
- **설정**: 모든 환경 변수는 `config/config.py`에서 `python-dotenv`로 한 번 로드
