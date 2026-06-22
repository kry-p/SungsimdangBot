# 배포 파이프라인

## 브랜치 전략

- `master` — production, GitHub Release 생성 시 배포
- `development` — 통합 브랜치, CI 실행
- `feature/*`, `fix/*`, `refactor/*` 등 — 작업 브랜치

## 배포 흐름

```
작업 브랜치 → PR → development (merge, 리뷰)
                      ↓
              PR → master (merge, 리뷰)
                      ↓
             GitHub Release 생성 (vX.Y.Z, --target master)
                      ↓
             CD 자동 실행:
               1. Release 태그에서 버전 추출 → VERSION build-arg로 전달
               2. Docker 빌드 (setuptools-scm이 build-arg 버전 반영, ARM64) → GHCR push
               3. 배포 서버에 SSH 배포
```

> 버전은 git 태그가 단일 진실 공급원이다. `pyproject.toml`에는 정적 버전 값이 없으며(`dynamic = ["version"]` + setuptools-scm), 별도 버전 bump 커밋/브랜치가 필요 없다.

## Release 절차

1. PR `development → master` 생성, 리뷰 후 머지
2. `gh release create vX.Y.Z --target master --generate-notes --title "vX.Y.Z"`

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
