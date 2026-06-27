# SungsimdangBot Claude Code Guide

이 리포지토리의 공통 에이전트 작업 규칙은 `AGENTS.md`가 단일 진실 공급원이다.
Claude Code에서 작업할 때도 먼저 `AGENTS.md`를 따른다.

## Claude-specific Notes

- `.claude/commands/`는 Claude Code용 반복 작업 레시피다.
- `.claude/rules/`의 세부 문서는 기존 Claude Code 호환을 위해 유지한다.
- `AGENTS.md`와 `.claude/rules/` 내용이 충돌하면, 사용자 지시가 없는 한 `AGENTS.md`를 우선한다.
- 커밋/PR/배포/설정 저장 규칙은 `AGENTS.md`와 `.claude/rules/`의 현재 내용을 함께 참고한다.
