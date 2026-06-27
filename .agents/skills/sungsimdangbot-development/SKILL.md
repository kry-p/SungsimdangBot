---
name: sungsimdangbot-development
description: Use when implementing, reviewing, or documenting SungsimdangBot repository changes to Telegram bot handlers, feature managers, user-facing strings, AI providers/settings, database models/migrations, external API models, tests, README, .env.example, AGENTS.md, Claude compatibility guidance, or Codex skills. Do not use for verification-only requests.
---

# SungsimdangBot Development

Use this skill for code and documentation changes in the SungsimdangBot repository. Treat `AGENTS.md` as the always-on repository rules and pair this with `$sungsimdangbot-checks` for verification.

## Start

1. Inspect related files before editing.
2. Preserve existing user changes in the worktree.
3. Keep changes scoped to the request.
4. Add or update tests based on behavior risk and blast radius.

## Code Style

- Use English identifiers in code and Korean for user-facing bot messages.
- Use `PascalCase` for classes, `snake_case` for functions, methods, instance variables, and module filenames, and `UPPER_SNAKE_CASE` for constants.
- Use absolute project imports such as `from modules.calculator import Calculator`.
- Keep import order as standard library, third-party packages, then project modules.
- Prefer `@staticmethod` for stateless feature helpers such as picker and coin toss style functions.

## Handler And Feature Work

- Register Telegram handlers in `bin/handlers.py`.
- Route feature logic through `BotFeaturesHub` in `modules/features_hub.py`.
- Use manager classes when a feature owns callbacks or bot interactions, following `AdminManager` and `LaftelService`.
- Wrap exception-prone handlers with `safe_handler`.
- Keep callback dispatch protected so handler failures do not stop polling.
- Log through `modules/log.py`'s `Logger` class.
- Return Korean error messages instead of raw exceptions for bot-facing feature failures.

## User-facing Strings

- Put new Korean user-facing messages in `resources/strings.py`.
- Avoid hardcoding new bot reply text inside feature modules.
- Follow `xxx_help_msg` and `xxx_error_msg` naming patterns where applicable.
- Domain constants used to map external API responses may stay in their module.

## AI Changes

- Keep provider implementations under `modules/ai/providers/`.
- Use `modules.ai.providers.base.AIProvider` as the provider contract.
- When adding or changing providers, update `AIChatManager._init_provider()`, `_PROVIDER_DEFAULT_MODELS`, `available_providers()`, admin provider UI, and tests together.
- Keep provider default models in each provider module's `DEFAULT_MODEL`.
- Convert provider exceptions into Korean user-facing strings in `resources/strings.py`.

## Settings And Database

- Use `config/config.py` for deployment-time environment variables and API keys.
- Use `Settings` for runtime settings with a module path constant such as `SETTINGS_MODULE_PATH = "modules.ai.chat"`.
- Store persistent data in `data/bot.db` via peewee models in `modules/database.py`.
- Current DB models are `Setting`, `AllowedChat`, `PendingAction`, and `RouletteGame`.
- For new tables, update `init_db()` and add tests. Add migrations when existing runtime data needs to move.

## External APIs

- Keep external request timeouts explicit.
- Parse structured responses with pydantic models in `modules/api_models.py` when practical. Prefer `model_validate_json()` for JSON response bodies.
- Keep tests network-independent by mocking external API calls.

## Documentation Changes

- Keep `AGENTS.md` as the source for cross-agent project rules.
- Keep `CLAUDE.md` as a thin Claude Code compatibility pointer.
- Keep Codex workflow details in `.agents/skills/`.
- Update README and `.env.example` when environment variables, commands, Python versions, CI/CD behavior, or module structure changes.

## Finish

Use `$sungsimdangbot-checks` for the narrowest useful verification before reporting completion. Use `$sungsimdangbot-git` when asked to commit, draft a PR, or prepare release/deployment work. Include changed files, verification results, and remaining risks in the final report.
