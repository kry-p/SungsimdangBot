import json
import os

from modules import log
from modules.database import AllowedChat, Setting, db

logger = log.Logger()

SETTINGS_JSON_PATH = os.path.join("data", "settings.json")
ALLOWLIST_JSON_PATH = os.path.join("data", "allowed_chats.json")
MIGRATION_MARKER = os.path.join("data", ".migrated")


def migrate_json_to_db():
    if os.path.exists(MIGRATION_MARKER):
        return

    migrated_any = False
    migrated_any |= _migrate_settings()
    migrated_any |= _migrate_allowlist()

    if migrated_any:
        with open(MIGRATION_MARKER, "w") as f:
            f.write("migrated")
        logger.log_info("JSON to SQLite migration completed.")


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
