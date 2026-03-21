# SungsimdangBot

텔레그램 봇(pyTelegramBotAPI) — 계산기, 랜덤 선택, 동전 던지기, 러시안 룰렛, 수온 알림, 검색, D-day, AI 질답(Gemini) 등 유틸리티 기능 제공.

## 프로젝트 구조

```
bin/main.py              # 진입점 — 봇 폴링 및 메시지 핸들러
config/
  __init__.py
  config.py              # 환경 변수(.env) 로더
modules/
  __init__.py
  features_hub.py        # BotFeaturesHub — 모든 기능 오케스트레이션
  calculator.py          # Calculator — 중위→후위 변환 수식 계산기
  database.py            # peewee ORM 모델 (Setting, AllowedChat, PendingAction, RouletteGame) + SQLite 초기화
  gemini_chat.py         # GeminiChat — Gemini AI 질답, 세션/레이트리밋 관리
  migration.py           # JSON → SQLite 일회성 마이그레이션
  random_based.py        # RandomBasedFeatures — 선택봇, 동전 던지기, 룰렛, 마법의 소라고동
  settings.py            # Settings — 런타임 설정 싱글톤 (SQLite 백엔드)
  web_based.py           # WebManager — 수온, 카카오/나무위키 검색
  log.py                 # Logger — 파일 + 콘솔 로깅
resources/
  __init__.py
  strings.py             # 모든 봇 메시지 문자열 및 인라인 키보드 (telebot import)
tests/
  __init__.py
  conftest.py            # pytest fixture (DB, 싱글톤 리셋)
  test_calculator.py     # Calculator 단위 테스트
  test_config.py         # config 단위 테스트
  test_database.py       # DB 모델 테스트
  test_features_hub.py   # BotFeaturesHub 통합 테스트 (mock bot)
  test_gemini_chat.py    # GeminiChat 단위 테스트
  test_log.py            # Logger 단위 테스트
  test_migration.py      # JSON→SQLite 마이그레이션 테스트
  test_random_based.py   # RandomBasedFeatures 단위 테스트
  test_settings.py       # Settings 단위 테스트
  test_web_based.py      # WebManager 단위 테스트
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

GitHub Actions (`ci.yml`) — `master`/`development` push 및 모든 PR에서 실행.

| Job | 내용 |
|-----|------|
| `ci` | Python 3.10 + 3.12 매트릭스: ruff check → ruff format --check → pytest --cov |
| `secrets` | gitleaks 시크릿 스캔 (전체 히스토리) |

- 테스트는 `pytest-cov`로 커버리지 측정 (`modules`, `config`, `resources` 대상)
- Python 3.12에서 `coverage.xml` 아티팩트 업로드

워크플로우 파일: `.github/workflows/ci.yml`

## CD

GitHub Actions (`cd.yml`) — GitHub Release 생성 시 실행.

```
development → PR → master (merge) → GitHub Release 생성
                                        ↓
                               CD workflow:
                                 1. pyproject.toml 버전 자동 업데이트
                                 2. Docker 이미지 빌드 (ARM64) → GHCR push (버전 태그 + latest)
                                 3. Tailscale VPN 연결
                                 4. SSH로 배포 서버 접속 → .env 갱신 + docker compose pull + up -d
```

| Job | 내용 |
|-----|------|
| `build-and-push` | Release 태그에서 버전 추출 → pyproject.toml 업데이트 → QEMU + Buildx로 ARM64 이미지 빌드, GHCR에 push |
| `deploy` | Tailscale VPN 연결 → SSH로 배포 서버에 .env 배포 + 컨테이너 재시작 |

워크플로우 파일: `.github/workflows/cd.yml`

### Docker

- `Dockerfile`: Python 3.12-slim 기반, `pip install .`로 설치
- `docker-compose.yml`: GHCR 이미지 pull, `.env` 파일로 환경변수 주입
- `.dockerignore`: 빌드 컨텍스트에서 불필요 파일 제외

### 필요한 GitHub Secrets

| Secret | 용도 |
|--------|------|
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth 클라이언트 ID |
| `TS_OAUTH_SECRET` | Tailscale OAuth 시크릿 |
| `PI_TAILSCALE_IP` | 배포 서버 Tailscale IP (100.x.y.z) |
| `PI_SSH_USER` | 배포 서버 SSH 사용자명 |
| `PI_SSH_KEY` | 배포 서버 SSH 개인키 |
| `PI_SSH_PORT` | 배포 서버 SSH 포트 |
| `BOT_TOKEN` | 텔레그램 봇 토큰 |
| `KAKAO_TOKEN` | 카카오 REST API 토큰 |
| `WEATHER_TOKEN` | OpenWeatherMap 토큰 |
| `SEOUL_HANGANG_WATER_TOKEN` | 서울 열린데이터 토큰 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `ADMIN_USER_ID` | 관리자 텔레그램 사용자 ID |

## 커밋 컨벤션

`.claude/rules/commit.md` 참조.

## 코드 컨벤션

`.claude/rules/code-style.md` 참조.
