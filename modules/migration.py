import json
import os

from modules import log
from modules.database import AllowedChat, Setting, db

logger = log.Logger()

SETTINGS_JSON_PATH = os.path.join("data", "settings.json")
ALLOWLIST_JSON_PATH = os.path.join("data", "allowed_chats.json")
MIGRATION_MARKER = os.path.join("data", ".migrated")
SETTINGS_PATH_MIGRATION_MARKER = os.path.join("data", ".settings_path_migrated")


def migrate_json_to_db():
    if os.path.exists(MIGRATION_MARKER):
        migrate_settings_path()
        return

    migrated_any = False
    migrated_any |= _migrate_settings()
    migrated_any |= _migrate_allowlist()

    if migrated_any:
        with open(MIGRATION_MARKER, "w") as f:
            f.write("migrated")
        logger.log_info("JSON to SQLite migration completed.")

    migrate_settings_path()


def _migrate_settings():
    if not os.path.exists(SETTINGS_JSON_PATH):
        return False
    try:
        with open(SETTINGS_JSON_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, TypeError):
        logger.log_error("Settings JSON corrupted, skipping migration.")
        return False

    rows = []
    _flatten_settings(data, [], rows)

    if rows:
        with db.atomic():
            for module_path, key, value in rows:
                Setting.replace(module_path=module_path, key=key, value=str(value)).execute()

    logger.log_info(f"Migrated {len(rows)} settings from JSON.")
    return True


def _flatten_settings(data, path_parts, rows):
    if not isinstance(data, dict):
        return
    for k, v in data.items():
        if isinstance(v, dict):
            _flatten_settings(v, path_parts + [k], rows)
        else:
            module_path = ".".join(path_parts)
            rows.append((module_path, k, v))


def _migrate_allowlist():
    if not os.path.exists(ALLOWLIST_JSON_PATH):
        return False
    try:
        with open(ALLOWLIST_JSON_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, TypeError):
        logger.log_error("Allowlist JSON corrupted, skipping migration.")
        return False

    if not data:
        return False

    with db.atomic():
        if isinstance(data[0], dict):
            for item in data:
                AllowedChat.replace(chat_id=item["id"], name=item.get("name", "")).execute()
        else:
            for chat_id in data:
                AllowedChat.replace(chat_id=chat_id, name="").execute()

    logger.log_info(f"Migrated {len(data)} allowed chats from JSON.")
    return True


def migrate_settings_path():
    """modules.gemini_chat 설정 경로를 modules.ai.chat으로 이전."""
    if os.path.exists(SETTINGS_PATH_MIGRATION_MARKER):
        return

    key_mapping = {
        "model": "model",
        "search_grounding": "search_enabled",
        "custom_prompt": "custom_prompt",
    }
    old_path = "modules.gemini_chat"
    new_path = "modules.ai.chat"

    migrated = 0
    with db.atomic():
        for old_key, new_key in key_mapping.items():
            row = Setting.get_or_none(Setting.module_path == old_path, Setting.key == old_key)
            if row:
                if not Setting.get_or_none(Setting.module_path == new_path, Setting.key == new_key):
                    Setting.replace(module_path=new_path, key=new_key, value=row.value).execute()
                    migrated += 1
                Setting.delete().where(Setting.module_path == old_path, Setting.key == old_key).execute()

        if not Setting.get_or_none(Setting.module_path == new_path, Setting.key == "provider"):
            Setting.replace(module_path=new_path, key="provider", value="gemini").execute()

    with open(SETTINGS_PATH_MIGRATION_MARKER, "w") as f:
        f.write("migrated")

    if migrated:
        logger.log_info(f"Settings path migration: {migrated} keys migrated from {old_path} to {new_path}.")
