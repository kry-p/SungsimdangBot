---
name: sungsimdangbot-git
description: Use when working in the SungsimdangBot repository on branches, commits, commit message formatting, PR drafts, PR creation, release planning, deployment flow, or GitHub release commands. Do not use for code implementation or verification-only requests.
---

# SungsimdangBot Git

Use this skill for branch, commit, PR, release, and deployment workflow tasks. Treat `AGENTS.md` as the always-on repository rules and pair this skill with `$sungsimdangbot-checks` when verification is needed.

## Branches

- Use `development` as the base branch for feature, fix, refactor, docs, chore, and test work.
- Open normal work PRs into `development`.
- Treat `development` to `master` as a separate release promotion process.
- Do not delete branches after PR merge unless the user explicitly asks.

## Commit Messages

Follow Conventional Commits:

```text
<type>: <description>
```

Allowed types:

- `feat`: 새 기능
- `fix`: 버그 수정
- `refactor`: 동작 변경 없는 리팩터링
- `docs`: 문서 변경
- `chore`: 빌드, 설정, 의존성
- `test`: 테스트 추가 또는 수정

Title rules:

- Use lowercase type, colon, and one space.
- Start the description with lowercase English.
- Use imperative present tense.
- Do not end with a period.
- Do not include `Co-Authored-By`.

Add a body when the title alone does not explain the change. Use this format:

```text
<type>: <description>

- 변경사항 1
- 변경사항 2

Why: 이 변경이 필요한 이유
```

Body rules:

- Write bullets with `-`.
- Write the body in Korean, keeping technical terms in English where natural.
- Include one `Why:` line.
- Omit the body only for simple changes such as typo fixes or import cleanup.

Before committing:

1. Confirm staged files with `git diff --cached --name-status`.
2. Confirm staged summary with `git diff --cached --stat`.
3. Ensure generated, secret, `.env`, DB, and log files are not staged.
4. Use `$sungsimdangbot-checks` for the narrowest useful verification.

## PR Drafts

Before drafting a PR:

1. Run `git log --oneline base..HEAD`.
2. Run `git diff --stat base..HEAD`.
3. Verify the PR draft matches the actual commits and diff.
4. Show the draft to the user and get approval before creating a PR.

PR target:

- Normal work branch: `development`
- Release promotion: `master`

PR title rules:

- Use a free-form descriptive English title.
- Start with uppercase.
- Do not prefix with a Conventional Commit type.
- Summarize the core change in one sentence.

PR body shape:

```markdown
## Summary
- 주요 변경사항 3~4줄 bullet

## Changes
### New Features / Bug Fixes / Refactoring / CI/CD 등
- 각 변경사항을 한 줄씩 기술

## Required GitHub Secrets (new)
- 추가/제거된 secret이 있을 때만 포함

## Test plan
- [x] 테스트 통과 여부 (개수, coverage)
- [x] lint/format 통과
- [x] 로컬 실행 확인
```

Use technical terms such as `rate limit`, `thread safety`, and `inline keyboard` as-is when that is clearer than translation.

## Release And Deployment

Production branch:

- `master` is production.
- GitHub Release publish triggers CD.
- Release tags use `vX.Y.Z`.
- Release target must be `master`.

Release flow:

```text
work branch -> PR -> development -> PR -> master -> GitHub Release -> CD
```

Create a release with:

```bash
gh release create vX.Y.Z --target master --generate-notes --title "vX.Y.Z"
```

Versioning:

- Major: breaking changes
- Minor: new features
- Patch: fixes and refactors
- Git tag is the single source of truth for version.
- `pyproject.toml` uses `dynamic = ["version"]` and `setuptools-scm`; do not create separate version bump commits unless requested.

CD behavior:

- Extract release version from the release tag.
- Pass it as Docker build arg `VERSION`.
- Build linux/amd64 and linux/arm64 images and push to GHCR.
- Connect to the deployment server through Tailscale and SSH.
- Update `.env`, pull the image, and run `docker compose up -d`.

CI/CD triggers:

- Pull request created or updated: CI runs.
- Push to `development`: CI runs.
- Push to `master`: CI runs.
- GitHub Release created: CD runs.
