# 배포 파이프라인

## 브랜치 전략

- `master` — production, GitHub Release 생성 시 배포
- `development` — 통합 브랜치, CI 실행
- `feature/*`, `fix/*`, `refactor/*` 등 — 작업 브랜치

## 배포 흐름

```
작업 브랜치 → PR → development (merge)
                      ↓
               development → PR → master (merge)
                                      ↓
                             GitHub Release 생성 (vX.Y.Z)
                                      ↓
                             CD 자동 실행:
                               1. Release 태그 버전을 빌드 컨텍스트 pyproject.toml에 반영 (master push 없음)
                               2. Docker 빌드 (amd64 + arm64) → GHCR push
                               3. 배포 서버에 SSH 배포
```

> master는 보호 브랜치라 CD가 버전 bump 커밋을 직접 push하지 않는다. master의 `pyproject.toml` 버전을 최신으로 유지하려면 release PR에서 직접 bump한다.

## Release 생성

- 태그 형식: `vX.Y.Z` (semver)
- **target은 반드시 `master`** — 다른 브랜치에서 Release를 생성하지 않음
- 릴리즈 노트에 주요 변경사항 기재
- 예: `gh release create vX.Y.Z --target master --title "vX.Y.Z"`

## CI/CD 트리거 조건

| 이벤트 | CI | CD |
|--------|----|----|
| PR 생성/업데이트 | 실행 | - |
| development push | 실행 | - |
| master push | 실행 | - |
| GitHub Release 생성 | - | 실행 |
