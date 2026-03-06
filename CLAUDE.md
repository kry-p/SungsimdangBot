# SungsimdangBot

텔레그램 봇(pyTelegramBotAPI) — 계산기, 랜덤 선택, 동전 던지기, 러시안 룰렛, 수온 알림, 검색, D-day, 비속어 감지 등 유틸리티 기능 제공.

## 프로젝트 구조

```
bin/main.py              # 진입점 — 봇 폴링 및 메시지 핸들러
config/config.py         # 환경 변수(.env) 로더
modules/
  features_hub.py        # BotFeaturesHub — 모든 기능 오케스트레이션
  calculator.py          # Calculator — 중위→후위 변환 수식 계산기
  random_based.py        # RandomBasedFeatures — 선택봇, 동전 던지기, 룰렛, 마법의 소라고동
  web_based.py           # WebManager — 수온, 카카오/나무위키 검색
  log.py                 # Logger — 파일 + 콘솔 로깅
  db_manager.py          # DatabaseManager (스텁)
  gaechu_info.py         # GaechuInfo (스텁)
resources/
  strings.py             # 모든 봇 메시지 문자열 및 인라인 키보드 (telebot import)
  users.py               # 사용자 정보 배열
tests/                   # pytest 테스트
```

## 개발 명령어

```bash
python3 -m venv .venv          # 가상환경 생성 (최초 1회)
source .venv/bin/activate      # 가상환경 활성화
pip install -e ".[dev]"        # 개발 의존성 포함 설치
pre-commit install             # git pre-commit 훅 설치 (최초 1회)
ruff check .                   # 린트
ruff format --check .          # 포맷 검사
pytest -v                      # 테스트 실행
```

## Pre-commit 훅

`git commit` 시 자동으로 ruff check + ruff format + gitleaks가 실행됩니다.
- 린팅 에러가 있으면 커밋이 차단됩니다.
- 자동 수정 가능한 이슈는 fix 후 커밋이 차단되므로, 수정된 파일을 `git add`한 뒤 다시 커밋하면 됩니다.
- **gitleaks**: 비밀 키(API 토큰, `.env` 파일 등)가 커밋에 포함되면 차단합니다. 의도적으로 허용이 필요한 경우 `#gitleaks:allow` 인라인 주석을 사용합니다.

## CI

GitHub Actions (`ci.yml`) — `master` push 및 모든 PR에서 실행.

| Job | 내용 |
|-----|------|
| `ci` | Python 3.9 + 3.12 매트릭스: ruff check → ruff format --check → pytest |
| `secrets` | gitleaks 시크릿 스캔 (전체 히스토리) |

워크플로우 파일: `.github/workflows/ci.yml`

## 알려진 이슈

- `Calculator.tokenize()` 75번째 줄 버그: `str.insert()` — 함수 호출 문법(`sqrt(4)`, `sin(0)` 등)이 작동하지 않음. 테스트에서 `xfail`로 표시.

## 커밋 컨벤션

Conventional Commits 형식을 따릅니다.

```
<type>: <description>
```

- **type**: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`
- type은 소문자, 콜론 + 공백 후 설명
- 설명은 영문 소문자 시작, 마침표 없음, 명령형 현재시제
- `Co-Authored-By` 시그니처 사용하지 않음

| type | 의미 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `refactor` | 리팩터링 (동작 변경 없음) |
| `docs` | 문서 변경 |
| `chore` | 빌드/설정/의존성 |
| `test` | 테스트 추가/수정 |

## 코드 컨벤션

### 네이밍 규칙

- **클래스**: PascalCase (`Calculator`, `BotFeaturesHub`, `WebManager`)
- **메서드/함수**: snake_case (`coin_toss`, `bad_word_detector`)
- **인스턴스 변수**: camelCase (레거시 컨벤션, 점진적으로 snake_case 전환 중) (`badWordCount`, `suonV2`)
- **상수**: UPPER_SNAKE_CASE (`BOT_TOKEN`, `DETECTOR_TIMEOUT`)
- **모듈 파일**: snake_case (`random_based.py`, `features_hub.py`)
- **언어**: 코드는 영문, 사용자 대상 메시지는 한국어

### import 패턴

- 크로스 패키지 import는 `sys.path.append()` 사용:
  ```python
  import os, sys
  sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
  ```
- 표준 라이브러리 → 서드파티 → 프로젝트 모듈 순서로 import

### 문자열 관리

- 모든 사용자 대상 메시지(한국어)는 `resources/strings.py`에 정의
- 모듈 코드에 사용자 대상 문자열을 하드코딩하지 않음 — `strings.xxx_msg` 참조
- 도움말 메시지 패턴: `strings.xxx_help_msg` / 에러 메시지 패턴: `strings.xxx_error_msg`

### 에러 처리

- 봇 기능은 raw exception 대신 한국어 에러 메시지를 반환
- 로깅은 `modules/log.py`의 Logger 클래스 사용

### 아키텍처 패턴

- **Hub 패턴**: `BotFeaturesHub`가 모든 기능 모듈의 인스턴스를 소유하고 위임
- **정적 메서드**: 상태 없는 기능 메서드(예: `picker`, `coin_toss`)는 `@staticmethod`
- **메시지 핸들러**: `bin/main.py`에서 `@bot.message_handler()` 데코레이터 사용
- **설정**: 모든 환경 변수는 `config/config.py`에서 `python-dotenv`로 한 번 로드
