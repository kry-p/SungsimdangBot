from unittest.mock import MagicMock

import pytest

from modules.database import AllowedChat, PendingAction, RouletteGame, Setting, db
from modules.settings import Settings


def make_message(text, chat_id=1, user_id=1):
    msg = MagicMock()
    msg.text = text
    msg.caption = None
    msg.photo = None
    msg.chat.id = chat_id
    msg.from_user.id = user_id
    msg.reply_to_message = None
    return msg


MODELS = [Setting, AllowedChat, PendingAction, RouletteGame]


@pytest.fixture(autouse=True)
def _reset_singleton():
    Settings._instance = None
    yield
    Settings._instance = None


@pytest.fixture(autouse=True)
def _test_db(_reset_singleton, tmp_path):
    db_path = str(tmp_path / "test.db")
    db.init(db_path)
    db.connect(reuse_if_open=True)
    db.create_tables(MODELS)
    yield db
    db.drop_tables(MODELS)
    db.close()
