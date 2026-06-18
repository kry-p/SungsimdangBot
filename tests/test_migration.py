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
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated")),
        ):
            migrate_json_to_db()

        # migrate_settings_path()가 modules.gemini_chat → modules.ai.chat으로 이동
        row = Setting.get_or_none((Setting.module_path == "modules.ai.chat") & (Setting.key == "model"))
        assert row is not None
        assert row.value == "gemini-2.5-pro"
        assert os.path.exists(marker_path)

    def test_no_json_file(self, tmp_path):
        marker_path = str(tmp_path / ".migrated")
        with (
            patch("modules.migration.SETTINGS_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.ALLOWLIST_JSON_PATH", str(tmp_path / "nonexistent2.json")),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated")),
        ):
            migrate_json_to_db()

        assert Setting.get_or_none(Setting.module_path == "modules.gemini_chat") is None
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
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated")),
        ):
            migrate_json_to_db()

        assert Setting.get_or_none(Setting.module_path == "modules.gemini_chat") is None


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
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated")),
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
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated")),
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
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated")),
        ):
            migrate_json_to_db()

        assert AllowedChat.select().count() == 0
        assert not os.path.exists(marker_path)


class TestMigration:
    def test_marker_prevents_repeat(self, tmp_path):
        json_path = str(tmp_path / "settings.json")
        marker_path = str(tmp_path / ".migrated")
        settings_path_marker = str(tmp_path / ".settings_path_migrated")
        data = {"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}
        with open(json_path, "w") as f:
            json.dump(data, f)
        with open(marker_path, "w") as f:
            f.write("migrated")
        with open(settings_path_marker, "w") as f:
            f.write("migrated")

        with (
            patch("modules.migration.SETTINGS_JSON_PATH", json_path),
            patch("modules.migration.ALLOWLIST_JSON_PATH", str(tmp_path / "nonexistent.json")),
            patch("modules.migration.MIGRATION_MARKER", marker_path),
            patch("modules.migration.SETTINGS_PATH_MIGRATION_MARKER", settings_path_marker),
        ):
            migrate_json_to_db()

        assert Setting.select().count() == 0


def test_migrate_settings_path(tmp_path, monkeypatch):
    from modules import migration
    from modules.database import Setting

    monkeypatch.setattr(migration, "SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated"))

    Setting.replace(module_path="modules.gemini_chat", key="model", value="gemini-2.5-pro").execute()
    Setting.replace(module_path="modules.gemini_chat", key="search_grounding", value="True").execute()
    Setting.replace(module_path="modules.gemini_chat", key="custom_prompt", value="Be brief.").execute()

    migration.migrate_settings_path()

    assert (
        Setting.get_or_none(Setting.module_path == "modules.ai.chat", Setting.key == "model").value == "gemini-2.5-pro"
    )
    assert (
        Setting.get_or_none(Setting.module_path == "modules.ai.chat", Setting.key == "search_enabled").value == "True"
    )
    assert (
        Setting.get_or_none(Setting.module_path == "modules.ai.chat", Setting.key == "custom_prompt").value
        == "Be brief."
    )
    assert Setting.get_or_none(Setting.module_path == "modules.ai.chat", Setting.key == "provider").value == "gemini"


def test_migrate_settings_path_idempotent(tmp_path, monkeypatch):
    from modules import migration

    monkeypatch.setattr(migration, "SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated"))

    migration.migrate_settings_path()
    migration.migrate_settings_path()  # should not raise


def test_migrate_settings_path_deletes_old_rows(tmp_path, monkeypatch):
    from modules import migration
    from modules.database import Setting

    monkeypatch.setattr(migration, "SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated"))

    Setting.replace(module_path="modules.gemini_chat", key="model", value="gemini-2.5-pro").execute()
    Setting.replace(module_path="modules.gemini_chat", key="search_grounding", value="False").execute()

    migration.migrate_settings_path()

    assert Setting.get_or_none(Setting.module_path == "modules.gemini_chat", Setting.key == "model") is None
    assert Setting.get_or_none(Setting.module_path == "modules.gemini_chat", Setting.key == "search_grounding") is None


def test_migrate_settings_path_does_not_overwrite_existing(tmp_path, monkeypatch):
    from modules import migration
    from modules.database import Setting

    monkeypatch.setattr(migration, "SETTINGS_PATH_MIGRATION_MARKER", str(tmp_path / ".settings_path_migrated"))

    # Simulate: DB committed but marker not written (crash scenario).
    # modules.ai.chat already has updated value; modules.gemini_chat still has old value.
    Setting.replace(module_path="modules.ai.chat", key="model", value="gemini-2.5-flash").execute()
    Setting.replace(module_path="modules.gemini_chat", key="model", value="gemini-2.5-pro").execute()

    migration.migrate_settings_path()

    assert (
        Setting.get_or_none(Setting.module_path == "modules.ai.chat", Setting.key == "model").value
        == "gemini-2.5-flash"
    )
