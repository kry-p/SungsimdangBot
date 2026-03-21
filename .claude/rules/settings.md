# 설정 저장 규칙

- 런타임에 변경되는 설정은 `modules/settings.py`의 `Settings` 싱글톤을 사용
- 환경변수(`config/config.py`)는 배포 시점 설정(API 키, 타임아웃 등)만 담당
- 설정 키는 모듈 경로 기반으로 접근
- 모듈 경로는 각 모듈 상단에 상수로 선언: `SETTINGS_MODULE_PATH = "modules.gemini_chat"`
- 사용 예: `Settings().get(SETTINGS_MODULE_PATH, "model", DEFAULT_MODEL)`
- 저장: `data/bot.db` SQLite (peewee ORM, Docker 볼륨으로 영속화)
- DB 모델 정의: `modules/database.py`의 `Setting`, `AllowedChat`
- `Settings`는 싱글톤이므로 `Settings()`로 어디서든 동일 인스턴스 접근
- 새 모듈에서 설정이 필요하면 동일 패턴으로 `SETTINGS_MODULE_PATH` 상수를 선언하여 사용
- 새 영속 데이터가 필요하면 `modules/database.py`에 peewee 모델을 추가하고 `init_db()`의 `create_tables`에 등록
