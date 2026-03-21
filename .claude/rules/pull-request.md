# PR 작성 규칙

## 대상 브랜치

- feature/fix/refactor 등 작업 브랜치 → `development` 으로 PR 생성
- `development` → `master` 는 별도 프로세스

## PR 제목

- 서술형 자유 형식 (Conventional Commits type 사용하지 않음)
- 영문, 대문자 시작
- 핵심 변경을 한 문장으로 요약
- 예: `Add Gemini AI chat and migrate data storage to SQLite`

## PR 본문 구조

```markdown
## Summary
- 주요 변경사항 3~4줄 bullet

## Changes
### 카테고리별 그룹핑 (New Features / Bug Fixes / Refactoring / CI/CD 등)
- 각 변경사항을 한 줄씩 기술

## Required GitHub Secrets (new)
- 추가/제거된 secret이 있을 때만 포함

## Test plan
- [x] 테스트 통과 여부 (개수, coverage)
- [x] lint/format 통과
- [x] 로컬 실행 확인
```

## 작성 절차

1. `git log --oneline base..HEAD`로 전체 커밋 확인
2. `git diff --stat base..HEAD`로 변경 파일 확인
3. 초안 작성 후 사용자에게 검토 요청
4. 초안의 각 항목이 실제 코드 변경과 일치하는지 검증
5. 승인 후 PR 생성

## 주의사항

- 기술 용어(rate limit, thread safety, inline keyboard 등)는 무리하게 한국어로 번역하지 않음
- PR 생성 전 반드시 초안을 사용자에게 보여주고 승인받을 것
