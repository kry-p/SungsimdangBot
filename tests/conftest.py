import pytest

from modules.database import AllowedChat, PendingAction, RouletteGame, Setting, db
from modules.settings import Settings

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
