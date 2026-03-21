import pytest
from peewee import IntegrityError

from modules.database import AllowedChat, PendingAction, RouletteGame, Setting


class TestSettingModel:
    def test_create_and_retrieve(self):
        Setting.create(module_path="modules.gemini_chat", key="model", value="gemini-2.5-pro")
        row = Setting.get((Setting.module_path == "modules.gemini_chat") & (Setting.key == "model"))
        assert row.value == "gemini-2.5-pro"

    def test_unique_constraint(self):
        Setting.create(module_path="m", key="k", value="v1")
        with pytest.raises(IntegrityError):
            Setting.create(module_path="m", key="k", value="v2")

    def test_replace_existing(self):
        Setting.replace(module_path="m", key="k", value="v1").execute()
        Setting.replace(module_path="m", key="k", value="v2").execute()
        row = Setting.get((Setting.module_path == "m") & (Setting.key == "k"))
        assert row.value == "v2"
        assert Setting.select().count() == 1


class TestAllowedChatModel:
    def test_create_and_retrieve(self):
        AllowedChat.create(chat_id=42, name="테스트")
        row = AllowedChat.get(AllowedChat.chat_id == 42)
        assert row.name == "테스트"

    def test_unique_chat_id(self):
        AllowedChat.replace(chat_id=1, name="A").execute()
        AllowedChat.replace(chat_id=1, name="B").execute()
        row = AllowedChat.get(AllowedChat.chat_id == 1)
        assert row.name == "B"
        assert AllowedChat.select().count() == 1

    def test_delete(self):
        AllowedChat.create(chat_id=1, name="test")
        AllowedChat.delete().where(AllowedChat.chat_id == 1).execute()
        assert AllowedChat.select().count() == 0


class TestPendingActionModel:
    def test_create_and_retrieve(self):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=1000.0)
        row = PendingAction.get(PendingAction.msg_id == 999)
        assert row.action == "allow"
        assert row.chat_id == 42

    def test_unique_msg_id(self):
        PendingAction.replace(msg_id=1, action="allow", chat_id=1, name="", timestamp=1.0).execute()
        PendingAction.replace(msg_id=1, action="deny", chat_id=2, name="", timestamp=2.0).execute()
        row = PendingAction.get(PendingAction.msg_id == 1)
        assert row.action == "deny"
        assert PendingAction.select().count() == 1

    def test_delete(self):
        PendingAction.create(msg_id=1, action="allow", chat_id=1, name="", timestamp=1.0)
        PendingAction.delete().where(PendingAction.msg_id == 1).execute()
        assert PendingAction.select().count() == 0


class TestRouletteGameModel:
    def test_create_and_retrieve(self):
        RouletteGame.create(chat_id=1, bullets="[true,false,false]")
        row = RouletteGame.get(RouletteGame.chat_id == 1)
        assert row.bullets == "[true,false,false]"

    def test_unique_chat_id(self):
        RouletteGame.replace(chat_id=1, bullets="[true]").execute()
        RouletteGame.replace(chat_id=1, bullets="[false]").execute()
        row = RouletteGame.get(RouletteGame.chat_id == 1)
        assert row.bullets == "[false]"
        assert RouletteGame.select().count() == 1

    def test_delete(self):
        RouletteGame.create(chat_id=1, bullets="[true]")
        RouletteGame.delete().where(RouletteGame.chat_id == 1).execute()
        assert RouletteGame.select().count() == 0
