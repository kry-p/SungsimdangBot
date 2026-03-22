# 커밋 컨벤션

Conventional Commits 형식을 따릅니다.

## 제목

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

## 본문

제목만으로 변경 의도가 충분히 전달되지 않을 때 본문을 작성합니다.
제목과 본문 사이에 빈 줄을 삽입합니다.

### 형식

```
<type>: <description>

- 변경사항 1
- 변경사항 2

Why: 이 변경이 필요한 이유
```

### 규칙

- 변경사항은 bullet(`-`)으로 나열
- `Why:` 줄에 변경 동기를 한 줄로 기술
- 본문 언어는 한국어, 기술 용어는 영어 그대로 사용 (예: entities, fallback, rate limit)
- 단순 변경(오타 수정, import 정리 등)에는 본문 생략

### 예시

```
feat: format Gemini responses as Telegram-rich text

- telegramify-markdown으로 Markdown → Telegram entities 변환
- 응답 분할을 entity 인식 기반으로 변경
- 변환 실패 시 plain text fallback 추가

Why: Gemini 응답의 코드블록, 볼드 등 서식이 표시되지 않던 문제 해결
```
