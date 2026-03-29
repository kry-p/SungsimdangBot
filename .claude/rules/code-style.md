# 코드 컨벤션

## 네이밍 규칙

- **클래스**: PascalCase (`Calculator`, `BotFeaturesHub`, `LaftelService`)
- **메서드/함수**: snake_case (`coin_toss`, `search_handler`)
- **인스턴스 변수**: snake_case (`schedule_cache`, `last_fetch_time`)
- **상수**: UPPER_SNAKE_CASE (`BOT_TOKEN`, `CACHE_INTERVAL`)
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
- 예외: 외부 API 응답값과 매핑하기 위한 한국어 상수(요일명 등)는 해당 모듈에 유지

## 에러 처리

- 봇 기능은 raw exception 대신 한국어 에러 메시지를 반환
- 로깅은 `modules/log.py`의 Logger 클래스 사용
- **핸들러 에러 바운더리**: 예외 가능 메시지 핸들러는 `safe_handler` 래퍼로 감싸서 예외를 로깅하고 사용자에게 에러 메시지 전송
- **콜백 에러 바운더리**: `handle_callback` 디스패치 로직 전체를 try-except으로 감싸서 예외 로깅

## 아키텍처 패턴

- **Hub 패턴**: `BotFeaturesHub`가 모든 기능 모듈의 인스턴스를 소유하고 위임
- **Feature Manager 패턴**: `AdminManager`, `LaftelService`처럼 `bot` 참조를 보유하고 자체 콜백 디스패치를 소유하는 모듈. Hub는 1줄 위임만 담당
- **정적 메서드**: 상태 없는 기능 메서드(예: `picker`, `coin_toss`)는 `@staticmethod`
- **메시지 핸들러**: `bin/handlers.py`의 `register_handlers()`에서 `@bot.message_handler()` 데코레이터로 등록
- **설정**: 모든 환경 변수는 `config/config.py`에서 `python-dotenv`로 한 번 로드
- **외부 API 응답 모델**: `modules/api_models.py`에 pydantic 모델로 정의, `model_validate_json()`으로 파싱하여 타입 안전성 확보
