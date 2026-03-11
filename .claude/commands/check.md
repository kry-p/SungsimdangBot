CI와 동일한 전체 검증을 순서대로 실행합니다.

1. `ruff check .` 실행 — PASS 또는 FAIL 보고
2. `ruff format --check .` 실행 — PASS 또는 FAIL 보고
3. `pytest -v` 실행 — PASS 또는 FAIL 보고
4. 모든 단계의 PASS/FAIL 요약 테이블 출력
5. 실패한 단계가 있으면 원인을 간략히 분석
