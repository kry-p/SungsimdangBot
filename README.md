# 성심당봇

<p>
    <img src="https://img.shields.io/badge/Python%203.10%2B-%233776AB?style=flat-square&logo=python&logoColor=white"/>&nbsp
    <img src="https://img.shields.io/badge/Telegram%20Bot-%2326A5E4?style=flat-square&logo=telegram&logoColor=white"/>&nbsp
</p>

텔레그램 이용자에게 편의기능을 제공하기 위한 봇, 성심당봇입니다.<br>
이 봇은 성심당과는 관계가 없습니다.

## 요구사항

- Python 3.10 이상
- Telegram Bot API 토큰
- 선택 기능별 외부 API 토큰

의존성은 `pyproject.toml`에서 관리합니다. 개발 환경에서는 아래 명령으로 설치합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

사용하는 주요 외부 API:

- Telegram Bot API: https://core.telegram.org/bots
- Kakao REST API: https://developers.kakao.com/docs
- OpenWeatherMap API: https://openweathermap.org/current
- 서울 열린데이터 광장: https://data.seoul.go.kr/dataList/OA-15488/S/1/datasetView.do
- Google Gemini API
- OpenAI API
- Laftel public API

## 프로젝트 구조

```text
bin/
  main.py                    # 엔트리포인트, DB 초기화, polling 시작
  handlers.py                # 텔레그램 command/callback/message handler 등록
config/
  config.py                  # 환경변수 기반 설정
modules/
  features_hub.py            # BotFeaturesHub, 기능 모듈 오케스트레이션
  admin.py                   # 관리자 UI, AI 설정, allowlist 관리
  ai/
    chat.py                  # AI 세션, provider 선택, rate limit, allowlist
    providers/
      base.py                # AIProvider protocol과 공통 예외
      gemini.py              # Gemini provider
      openai.py              # OpenAI provider
  api_models.py              # 외부 API pydantic 응답 모델
  calculator.py              # 수식 계산기
  database.py                # peewee ORM 모델과 SQLite 초기화
  laftel.py                  # Laftel 편성표, 랭킹, 검색
  migration.py               # JSON에서 SQLite로 일회성 마이그레이션
  random_based.py            # 선택봇, 동전 던지기, 러시안 룰렛, 마법의 소라고동
  settings.py                # 런타임 설정 싱글톤
  web_based.py               # 수온, Kakao/나무위키 검색, 위치/날씨, RSS
resources/
  strings.py                 # 봇 메시지 문자열과 inline keyboard
tests/
  conftest.py                # pytest fixture, 임시 DB, singleton reset
```

에이전트 작업 규칙은 `AGENTS.md`를 기준으로 합니다. Codex 반복 검증 workflow는 `.agents/skills/sungsimdangbot-checks`에, 구현 workflow는 `.agents/skills/sungsimdangbot-development`에, git/PR/release workflow는 `.agents/skills/sungsimdangbot-git`에 있습니다. Claude Code 호환 문서는 `CLAUDE.md`와 `.claude/`에 있습니다.

## 실행 방법

### 1. 환경변수 설정

프로젝트 루트에 `.env` 파일을 만들고 필요한 값을 설정합니다. 예시는 `.env.example`을 참고하세요.

```bash
cp .env.example .env
```

최소 실행에는 `BOT_TOKEN`이 필요합니다. 외부 API를 사용하는 기능은 해당 토큰이 없으면 정상 동작하지 않을 수 있습니다.

### 2. 로컬 실행

```bash
python bin/main.py
```

### Docker로 실행

로컬 테스트용 이미지는 직접 빌드해서 실행합니다.

```bash
docker build -t sungsimdangbot:local .
docker run -d --name sungsimdangbot --env-file .env -v "$(pwd)/data:/app/data" sungsimdangbot:local
docker logs sungsimdangbot --tail 10
docker rm -f sungsimdangbot
```

`docker-compose.yml`은 GHCR production 이미지를 pull하는 배포용 설정입니다.

```bash
docker compose up -d
```

## 기능 목록

모든 기능은 그룹에서도 사용할 수 있지만, 봇에게 그룹 입장과 메시지 접근 권한을 부여해야 합니다. 해당 권한은 텔레그램 `@BotFather`에서 수정할 수 있습니다.

- 한강 수온 알림: `수온` 또는 `자살` 키워드가 포함된 메시지에 현재 한강 수온을 응답
- 선택봇: `/pick` 뒤에 입력한 단어 중 하나를 무작위 선택
- 러시안 룰렛: `/roulette`, `/shoot`, `/flush_bullet`
- 동전뒤집기: `/coin_toss`
- 현재 위치 정보: 텔레그램 위치 메시지에 주소, 좌표, 날씨 응답
- D-day: `/dday YYYY M D`
- 계산기: `/calc sin ( pi / 2 )`
- 검색: `/search`
- 나무위키 검색: `/namu`
- AI 질문: `/ask`, 이미지 caption 또는 사진 reply 지원
- AI 대화 초기화: `/clear_chat`
- AI 설정 확인/변경: `/ask_settings`
- 내 사용자 ID 확인: `/myid`
- 봇 상태 확인: `/ping`
- Laftel 정보: `/laftel`
- 번역 RSS 수신: `/bfrss`
- 마법의 소라고동: `마법의 소라고둥` 또는 `마법의 소라고동` 키워드 응답

AI 질문 기능은 allowlist에 등록된 채팅에서만 사용할 수 있습니다. 관리자는 `ADMIN_USER_ID`로 지정하며 `/allow_chat`, `/deny_chat`, `/ask_settings` 명령으로 채팅과 AI 설정을 관리합니다.

## 환경변수

프로젝트 루트의 `.env` 파일에 아래 환경변수를 설정합니다. `필수`로 표시된 값은 반드시 필요합니다.

| 변수명 | 필수 | 설명 |
|--------|------|------|
| `BOT_TOKEN` | 필수 | 텔레그램 봇 API 토큰 |
| `KAKAO_TOKEN` | | Kakao REST API 토큰, 위치 정보와 검색 기능 |
| `WEATHER_TOKEN` | | OpenWeatherMap 토큰, 위치 기반 날씨 정보 |
| `SEOUL_HANGANG_WATER_TOKEN` | | 서울 열린데이터 광장 토큰, 한강 수온 정보 |
| `GEMINI_API_KEY` | | Gemini AI provider 사용 시 필요 |
| `OPENAI_API_KEY` | | OpenAI AI provider 사용 시 필요 |
| `OPENAI_BASE_URL` | | OpenAI 호환 endpoint, 기본값 `https://api.openai.com/v1` |
| `AI_SESSION_TIMEOUT` | | AI 세션 만료 시간(초), 기본값 `3600` |
| `AI_MAX_HISTORY` | | AI provider history 보관 턴 수, 기본값 `20` |
| `AI_RATE_LIMIT` | | 채팅/사용자별 분당 AI 요청 제한, 기본값 `5` |
| `AI_API_TIMEOUT` | | AI API 요청 timeout(초), 기본값 `60` |
| `ADMIN_USER_ID` | | 관리자 텔레그램 사용자 ID |
| `RSSF_TOKEN` | | RSS 번역 서버 인증 토큰 |
| `RSSF_URL` | | RSS 번역 서버 URL |

`AI_*` 값이 없으면 이전 Gemini 전용 이름인 `GEMINI_SESSION_TIMEOUT`, `GEMINI_MAX_HISTORY`, `GEMINI_RATE_LIMIT`, `GEMINI_API_TIMEOUT`도 fallback으로 읽습니다.

## 개발 명령어

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -v
```

pre-commit hook:

```bash
pre-commit install
```

`git commit` 시 ruff check, ruff format, gitleaks가 실행됩니다.

## CI/CD

CI는 GitHub Actions에서 `master`, `development`, 모든 PR에 대해 실행됩니다.

| Job | 내용 |
|-----|------|
| `ci` | Python 3.10 + 3.14 matrix, ruff check, ruff format check, pytest coverage |
| `secrets` | gitleaks secret scan |

CD는 GitHub Release publish 이벤트에서 실행됩니다.

1. Release tag `vX.Y.Z`에서 버전을 추출합니다.
2. Docker image를 linux/amd64, linux/arm64로 빌드해 GHCR에 push합니다.
3. Tailscale VPN으로 배포 서버에 접근합니다.
4. SSH로 `.env`와 compose 상태를 갱신한 뒤 컨테이너를 재시작합니다.

버전은 git tag가 단일 진실 공급원입니다. `pyproject.toml`은 `dynamic = ["version"]`와 `setuptools-scm`을 사용합니다.

## 필요한 GitHub Secrets

| Secret | 용도 |
|--------|------|
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth 클라이언트 ID |
| `TS_OAUTH_SECRET` | Tailscale OAuth 시크릿 |
| `PI_TAILSCALE_IP` | 배포 서버 Tailscale IP |
| `PI_SSH_USER` | 배포 서버 SSH 사용자명 |
| `PI_SSH_KEY` | 배포 서버 SSH 개인키 |
| `PI_SSH_PORT` | 배포 서버 SSH 포트 |
| `BOT_TOKEN` | 텔레그램 봇 토큰 |
| `KAKAO_TOKEN` | Kakao REST API 토큰 |
| `WEATHER_TOKEN` | OpenWeatherMap 토큰 |
| `SEOUL_HANGANG_WATER_TOKEN` | 서울 열린데이터 토큰 |
| `GEMINI_API_KEY` | Gemini API 키 |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `OPENAI_BASE_URL` | OpenAI 호환 endpoint |
| `ADMIN_USER_ID` | 관리자 텔레그램 사용자 ID |
| `RSSF_TOKEN` | RSS 번역 서버 인증 토큰 |
| `RSSF_URL` | RSS 번역 서버 URL |

## 기여자

- [@h1ghg3n](https://github.com/h1ghg3n) - 공동 개발

## FAQ

Q. 봇은 어떻게 만드나요?

먼저 텔레그램 계정이 있어야 합니다. [BotFather](https://t.me/BotFather)의 안내를 따르면 됩니다. 아이디가 `@BotFather`가 아닌 계정은 사칭이니 주의하세요.
