import pytest

from modules.database import AllowedChat, Setting, db
from modules.settings import Settings

MODELS = [Setting, AllowedChat]


@pytest.fixture(autouse=True)
def _test_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    db.init(db_path)
    db.connect()
    db.create_tables(MODELS)
    yield db
    db.drop_tables(MODELS)
    db.close()


@pytest.fixture(autouse=True)
def _reset_singleton():
    Settings._instance = None
    yield
    Settings._instance = None
