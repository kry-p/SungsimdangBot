# 배포 파이프라인

## 브랜치 전략

- `master` — production, GitHub Release 생성 시 배포
- `development` — 통합 브랜치, CI 실행
- `feature/*`, `fix/*`, `refactor/*` 등 — 작업 브랜치
- `release/vX.Y.Z` — 버전 bump 전용 브랜치

## 배포 흐름

```
작업 브랜치 → PR → development (merge)
                      ↓
              release/vX.Y.Z 브랜치 생성 (from development)
                      │
                      ├─ pyproject.toml 버전 bump 커밋
                      │
                      ├─→ PR → development (merge) ← 버전이 development에 반영
                      │
                      └─→ PR → master (merge)
                                    ↓
                           GitHub Release 생성 (vX.Y.Z)
                                    ↓
                           CD 자동 실행:
                             1. Release 태그 버전을 빌드 컨텍스트 pyproject.toml에 반영 (master push 없음)
                             2. Docker 빌드 (ARM64) → GHCR push
                             3. 배포 서버에 SSH 배포
```

> release 브랜치는 development와 master 양쪽에 머지해 버전이 두 브랜치에 모두 반영되도록 한다.

## Release 절차

1. `development`에서 `release/vX.Y.Z` 브랜치 생성
2. `pyproject.toml` 버전 bump 커밋 (`chore: bump version to X.Y.Z`)
3. PR `release/vX.Y.Z → development` 생성 및 머지
4. PR `release/vX.Y.Z → master` 생성 및 머지
5. `gh release create vX.Y.Z --target master --generate-notes --title "vX.Y.Z"`

## 버전 관리 (Semver)

| 변경 | 버전 |
|------|------|
| 호환성 깨지는 변경 | Major (X) |
| 새 기능 추가 | Minor (Y) |
| 버그 수정, 리팩터링 | Patch (Z) |

## Release 생성

- 태그 형식: `vX.Y.Z` (semver)
- **target은 반드시 `master`** — 다른 브랜치에서 Release를 생성하지 않음
- 릴리즈 노트: `--generate-notes`로 자동 생성
- 예: `gh release create vX.Y.Z --target master --generate-notes --title "vX.Y.Z"`

## CI/CD 트리거 조건

| 이벤트 | CI | CD |
|--------|----|----|
| PR 생성/업데이트 | 실행 | - |
| development push | 실행 | - |
| master push | 실행 | - |
| GitHub Release 생성 | - | 실행 |
