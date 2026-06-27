---
name: sungsimdangbot-checks
description: Use when working in the SungsimdangBot repository to run or explain lint, format, test, CI-equivalent check, local bot run, local Docker run, dependency synchronization, or PR-ready verification workflows. Do not use for feature implementation details except verification.
---

# SungsimdangBot Checks

Use this skill for repeatable verification and local execution workflows. Treat `AGENTS.md` as the always-on repository rules.

## Start

1. Confirm branch and worktree with `git status --short` and `git branch --show-current` when verification is part of a larger change.
2. If `.venv/bin/python` does not exist, create and sync the development environment:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -e ".[dev]"
   ```

3. Use `.venv/bin/...` commands after the environment exists.
4. Report each command's PASS/FAIL and summarize important failures.

## lint

Run ruff lint and format checks:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Ask before applying auto-fixes with `ruff check --fix .` or `ruff format .`.

## test

Run the pytest suite:

```bash
.venv/bin/python -m pytest -v
```

If collection fails with an import error, check whether `.venv` is synchronized with `pyproject.toml`. The usual fix is:

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

If pytest creates temporary directories named `pytest-of-*` in the project root, clean up only those generated test directories after the test run.

## check

Run the same local verification sequence as CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -v --cov --cov-report=term-missing --cov-report=xml
```

Use this for shared behavior, code changes, or pre-PR verification.

## run

Run the bot locally only when the user asks for it:

1. Confirm `.env` exists in the project root. If it is missing, stop and report that `BOT_TOKEN` is required.
2. Install runtime dependencies if needed:

   ```bash
   .venv/bin/python -m pip install -e .
   ```

   Use `.venv/bin/python -m pip install -e ".[dev]"` instead when tests or dev tools are also needed.

3. Start the bot:

   ```bash
   .venv/bin/python bin/main.py
   ```

Do not leave long-running bot processes active at the end of the turn unless the user asked for that.

## docker-local

Use Docker for local container verification only when requested.

`docker-compose.yml` pulls the GHCR production image, so local testing should build a local image first:

```bash
docker build -t sungsimdangbot:local .
docker run -d --name sungsimdangbot --env-file .env -v "$(pwd)/data:/app/data" sungsimdangbot:local
docker logs sungsimdangbot --tail 10
docker rm -f sungsimdangbot
```

Rules:

- Confirm `.env` exists before running the container.
- Mount `./data:/app/data` so SQLite data is persistent.
- If a container named `sungsimdangbot` already exists, ask before removing it unless the user explicitly requested cleanup.
- Local builds default to version `0.0.0`; pass `--build-arg VERSION=X.Y.Z` only when a specific version is needed.

## Docs-only Verification

For documentation-only changes, at least run:

```bash
git diff --check
```

Run broader checks only when the docs change executable commands, packaging, CI/CD, or environment setup.
