# 커밋 컨벤션

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
