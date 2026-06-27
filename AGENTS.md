# SungsimdangBot Agent Guide

이 문서는 Codex와 Claude Code 등 코딩 에이전트가 공유하는 프로젝트 작업 규칙이다.
도구별 파일이 있어도 프로젝트 전반 규칙은 이 파일을 우선한다.
반복 검증 workflow는 Codex skill `.agents/skills/sungsimdangbot-checks`에, 구현 workflow는 `.agents/skills/sungsimdangbot-development`에, git/PR/release workflow는 `.agents/skills/sungsimdangbot-git`에 정의되어 있다.

## Project Overview

SungsimdangBot은 pyTelegramBotAPI 기반 텔레그램 봇이다. 계산기, 랜덤 선택, 동전 던지기,
러시안 룰렛, 한강 수온, 위치 기반 날씨/주소, 검색, D-day, Laftel 조회, RSS 번역 수신,
Gemini/OpenAI 기반 AI 질답을 제공한다.

주요 진입점과 구조:

- `bin/main.py`: 환경변수 검증, DB 초기화, JSON 마이그레이션, 봇 polling 시작
- `bin/handlers.py`: 텔레그램 command, callback, message handler 등록
- `config/config.py`: `.env`와 환경변수 로드, 외부 endpoint와 timeout 설정
- `modules/features_hub.py`: `BotFeaturesHub`가 기능 모듈을 소유하고 handler 요청을 위임
- `modules/ai/chat.py`: AI provider 선택, 세션, allowlist, rate limit, admin 설정 저장
- `modules/ai/providers/`: Gemini/OpenAI provider 구현과 공통 protocol
- `modules/admin.py`: AI 설정, allowlist, provider/model/search/prompt 관리자 UI
- `modules/database.py`: peewee 모델과 SQLite 초기화
- `modules/settings.py`: 런타임 설정 싱글톤
- `modules/web_based.py`: Kakao, OpenWeatherMap, 서울 열린데이터, RSS 요청
- `modules/laftel.py`: Laftel 편성표, 랭킹, 검색
- `resources/strings.py`: 사용자 대상 메시지와 inline keyboard
- `tests/`: pytest 단위/통합 테스트, 임시 SQLite DB fixture

## Setup And Commands

가상환경이 있으면 `.venv/bin/...` 명령을 우선 사용한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

자주 쓰는 검증 명령:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -v
```

CI와 동일한 전체 검증 순서:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -v --cov --cov-report=term-missing --cov-report=xml
```

로컬 실행:

```bash
python bin/main.py
```

로컬 실행에는 프로젝트 루트의 `.env`가 필요하다. 최소 필수 값은 `BOT_TOKEN`이다.

## Shared Command Recipes

이 섹션은 항상 자동으로 읽혀야 하는 기본 명령 레시피다.
Codex에서 반복 검증 workflow가 필요하면 `$sungsimdangbot-checks` skill을 사용한다.
기능 구현, handler, AI provider, DB, 외부 API 모델 변경에는 `$sungsimdangbot-development` skill을 사용한다.
commit, PR, release, deployment workflow에는 `$sungsimdangbot-git` skill을 사용한다.

### lint

프로젝트에 ruff 린터와 포맷 검사를 실행한다.

1. `.venv/bin/ruff check .` 실행
2. `.venv/bin/ruff format --check .` 실행
3. 각 단계별 결과 보고
4. 자동 수정 가능한 이슈가 있으면 `ruff check --fix .` 및 `ruff format .` 적용 여부를 사용자에게 확인

### test

프로젝트 테스트를 실행한다.

1. `.venv` 가상환경이 있으면 `.venv/bin/python -m pytest -v` 실행
2. 테스트 결과 요약 보고: passed, failed, error 수
3. 실패한 테스트가 있으면 원인을 간략히 분석
4. 의존성 import error가 나면 `.venv`가 `pyproject.toml`과 동기화되지 않았는지 확인

### check

CI와 동일한 전체 검증을 순서대로 실행한다.

1. `.venv/bin/ruff check .` 실행
2. `.venv/bin/ruff format --check .` 실행
3. `.venv/bin/python -m pytest -v --cov --cov-report=term-missing --cov-report=xml` 실행
4. 모든 단계의 PASS/FAIL 요약 출력
5. 실패한 단계가 있으면 원인을 간략히 분석

### run

봇을 로컬에서 실행한다.

1. 프로젝트 루트에 `.env` 파일이 있는지 확인한다. 없으면 경고 후 중단
2. 필요 시 `.venv/bin/python -m pip install -e .`로 의존성 설치
3. `.venv/bin/python bin/main.py` 실행

Docker local test:

```bash
docker build -t sungsimdangbot:local .
docker run -d --name sungsimdangbot --env-file .env -v "$(pwd)/data:/app/data" sungsimdangbot:local
docker logs sungsimdangbot --tail 10
docker rm -f sungsimdangbot
```

`docker-compose.yml`은 GHCR production 이미지를 pull하는 용도다. 로컬 테스트는 직접 build한 이미지를 사용한다.

## Code Conventions

- 코드는 영어 식별자를 사용하고, 사용자에게 보이는 봇 메시지는 한국어로 작성한다.
- 클래스는 `PascalCase`, 함수/메서드/인스턴스 변수는 `snake_case`, 상수는 `UPPER_SNAKE_CASE`를 사용한다.
- 모듈 파일명은 `snake_case.py`를 사용한다.
- import는 표준 라이브러리, 서드파티, 프로젝트 모듈 순서로 정렬한다.
- 프로젝트 내부 import는 `from modules.calculator import Calculator` 같은 절대 import를 사용한다.
- 모든 사용자 대상 메시지는 `resources/strings.py`에 둔다. 모듈 내부에 새 한국어 응답 문자열을 하드코딩하지 않는다.
- 도움말 메시지는 `xxx_help_msg`, 에러 메시지는 `xxx_error_msg` 패턴을 따른다.
- 외부 API의 한국어 응답값 매핑 같은 도메인 상수는 해당 모듈에 둘 수 있다.

## Architecture Rules

- `BotFeaturesHub`는 기능 모듈 인스턴스를 소유하고 얇게 위임한다. 새 기능도 가능하면 이 패턴을 따른다.
- `AdminManager`, `LaftelService`처럼 bot 참조와 자체 callback dispatch가 필요한 기능은 Feature Manager로 분리한다.
- 메시지 handler는 `bin/handlers.py`의 `register_handlers()`에서 등록한다.
- 예외 가능 handler에는 `safe_handler`를 적용해 로깅하고 `strings.generic_error_msg` 계열 응답을 보낸다.
- callback dispatch 전체도 예외 boundary 안에 두어 handler 실패가 polling을 죽이지 않게 한다.
- 외부 API 응답은 가능한 `modules/api_models.py`의 pydantic 모델로 파싱한다.
- `requests` 호출에는 timeout을 둔다. 기존 외부 API 호출은 보통 `timeout=10`이다.

## AI Provider Rules

- AI 기능은 `modules.ai.providers.base.AIProvider` protocol을 기준으로 구현한다.
- 새 provider를 추가하면 `AIChatManager._init_provider()`, `_PROVIDER_DEFAULT_MODELS`,
  `available_providers()`, admin provider 선택 UI, tests를 함께 갱신한다.
- provider별 기본 모델은 provider 모듈의 `DEFAULT_MODEL`에 둔다.
- 세션 만료, history trim, search toggle, image input 지원 여부를 provider 테스트로 검증한다.
- 사용자-facing AI 응답 실패는 raw exception 대신 `resources/strings.py`의 한국어 메시지로 변환한다.

## Settings And Data

- 배포 시점 설정과 API key는 `config/config.py`의 환경변수로 관리한다.
- 런타임에 변경되는 설정은 `modules/settings.py`의 `Settings` 싱글톤을 사용한다.
- 설정 키는 모듈 경로 기반으로 저장한다. 예: `SETTINGS_MODULE_PATH = "modules.ai.chat"`.
- 저장소는 `data/bot.db` SQLite이며 Docker에서는 `./data:/app/data` 볼륨으로 영속화한다.
- 새 영속 데이터가 필요하면 `modules/database.py`에 peewee 모델을 추가하고 `init_db()`의 `create_tables`에 등록한다.
- 기존 JSON 데이터 마이그레이션은 `modules/migration.py`의 marker 파일 규칙을 유지한다.

## Testing Rules

- 테스트는 외부 네트워크에 의존하지 않게 mock한다.
- DB 테스트는 `tests/conftest.py`의 임시 SQLite fixture를 사용한다.
- singleton 상태를 쓰는 코드(`Settings` 등)는 테스트 사이에 reset되도록 fixture를 확인한다.
- behavior 변경에는 가까운 단위 테스트를 추가하고, handler routing 변경에는 `tests/test_handlers.py` 또는 관련 manager 테스트를 갱신한다.
- `.venv`가 `pyproject.toml`과 동기화되지 않아 import error가 나면 먼저 `pip install -e ".[dev]"`로 의존성을 맞춘다.

## Git And PR Rules

- 작업 브랜치는 `development`에서 만든다. PR 대상도 `development`다.
- `development`에서 `master`로 가는 PR과 release는 별도 프로세스다.
- commit message는 Conventional Commits 형식을 따른다: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`.
- 제목은 `<type>: <description>` 형식, 영문 소문자 시작, 마침표 없음, 명령형 현재시제를 사용한다.
- `Co-Authored-By` 시그니처는 사용하지 않는다.
- PR 제목은 Conventional Commit type 없이 영문 대문자 시작의 서술형 제목을 사용한다.
- PR 본문에는 Summary, Changes, Required GitHub Secrets(new), Test plan을 필요에 맞게 포함한다.
- PR 생성 전 초안을 사용자에게 보여주고 승인을 받는다.
- PR merge 후 브랜치를 삭제하지 않는다.

## CI/CD

- CI는 GitHub Actions에서 `master`, `development`, 모든 PR에 대해 실행된다.
- CI matrix는 Python 3.10과 3.14를 사용하며 `ruff check`, `ruff format --check`, pytest coverage를 실행한다.
- CD는 GitHub Release publish 이벤트에서 실행된다.
- release tag `vX.Y.Z`에서 version을 추출해 Docker build arg `VERSION`으로 전달한다.
- Docker 이미지는 `python:3.14-slim` 기반이며 linux/amd64, linux/arm64로 GHCR에 push된다.
- 배포 job은 Tailscale과 SSH로 서버에 접속해 `.env`를 갱신하고 `docker compose pull && docker compose up -d`를 실행한다.
- 버전은 git tag가 단일 진실 공급원이다. `pyproject.toml`은 `dynamic = ["version"]`와 `setuptools-scm`을 사용한다.

## Agent Workflow

- 수정 전 관련 파일을 읽고 기존 패턴을 따른다.
- 사용자 변경이 섞여 있으면 되돌리지 말고, 필요한 경우 그 변경 위에서 작업한다.
- 변경 범위는 요청에 맞게 좁게 유지한다. 무관한 리팩터링은 별도 요청이 없으면 하지 않는다.
- 비밀 값, `.env`, `data/bot.db`, log 파일은 커밋하지 않는다.
- 검증 명령을 실행한 뒤 결과를 요약한다. 실행하지 못한 검증은 이유를 분명히 적는다.
- Codex에서 lint/test/check/run 같은 반복 검증 workflow를 수행할 때는 가능한 `$sungsimdangbot-checks` skill을 사용한다.
- Codex에서 기능 구현, handler, AI provider, DB, 외부 API 모델 변경을 수행할 때는 가능한 `$sungsimdangbot-development` skill을 사용한다.
- Codex에서 commit, PR, release, deployment workflow를 수행할 때는 가능한 `$sungsimdangbot-git` skill을 사용한다.
- 외부 API, GitHub Actions, Codex 동작처럼 현재성이 중요한 사실은 최신 공식 문서나 실제 파일로 확인한다.
