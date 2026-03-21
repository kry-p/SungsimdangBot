import json
import os
from unittest.mock import patch

from modules.database import AllowedChat, Setting
from modules.migration import (
    migrate_json_to_db,
)


class TestMigrateSettings:
    def test_nested_settings(self, tmp_path):
        json_path = str(tmp_path / "settings.json")
        marker_path = str(tmp_path / ".migrated")
        data = {"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}
        with open(json_path, "w") as f:
            json.dump(data, f)

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", json_path),
            patch("modules.migration.ALLOWLIST_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        row = Setting.get_or_none((Setting.module_path == "modules.gemini_chat") & (Setting.key == "model"))
        assert row is not None
        assert row.value == "gemini-2.5-pro"
        assert os.path.exists(marker_path)

    def test_no_json_file(self, tmp_path):
        marker_path = str(tmp_path / ".migrated")
        with (
            patch("modules.migration.SETTINGS_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.ALLOWLIST_JSON_PATH", str(tmp_path / "nonexistent2.json")),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        assert Setting.select().count() == 0
        assert not os.path.exists(marker_path)

    def test_corrupted_json(self, tmp_path):
        json_path = str(tmp_path / "settings.json")
        marker_path = str(tmp_path / ".migrated")
        with open(json_path, "w") as f:
            f.write("not json")

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", json_path),
            patch("modules.migration.ALLOWLIST_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        assert Setting.select().count() == 0


class TestMigrateAllowlist:
    def test_new_format(self, tmp_path):
        json_path = str(tmp_path / "allowed_chats.json")
        marker_path = str(tmp_path / ".migrated")
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        with open(json_path, "w") as f:
            json.dump(data, f)

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.ALLOWLIST_JSON_PATH", json_path),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        assert AllowedChat.select().count() == 2
        row = AllowedChat.get(AllowedChat.chat_id == 1)
        assert row.name == "A"

    def test_legacy_format(self, tmp_path):
        json_path = str(tmp_path / "allowed_chats.json")
        marker_path = str(tmp_path / ".migrated")
        with open(json_path, "w") as f:
            json.dump([1, 2, 3], f)

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.ALLOWLIST_JSON_PATH", json_path),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        assert AllowedChat.select().count() == 3
        row = AllowedChat.get(AllowedChat.chat_id == 1)
        assert row.name == ""

    def test_empty_list(self, tmp_path):
        json_path = str(tmp_path / "allowed_chats.json")
        marker_path = str(tmp_path / ".migrated")
        with open(json_path, "w") as f:
            json.dump([], f)

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.ALLOWLIST_JSON_PATH", json_path),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        assert AllowedChat.select().count() == 0
        assert not os.path.exists(marker_path)


class TestMigration:
    def test_marker_prevents_repeat(self, tmp_path):
        json_path = str(tmp_path / "settings.json")
        marker_path = str(tmp_path / ".migrated")
        data = {"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}
        with open(json_path, "w") as f:
            json.dump(data, f)
        with open(marker_path, "w") as f:
            f.write("migrated")

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", json_path),
            patch("modules.migration.ALLOWLIST_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
        ):
            migrate_json_to_db()

        assert Setting.select().count() == 0
