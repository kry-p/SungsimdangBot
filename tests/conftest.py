import pytest
from peewee import SqliteDatabase

from modules.database import AllowedChat, Setting

MODELS = [Setting, AllowedChat]


@pytest.fixture(autouse=True)
def _test_db():
    test_db = SqliteDatabase(":memory:")
    with test_db.bind_ctx(MODELS):
        test_db.create_tables(MODELS)
        yield test_db
        test_db.drop_tables(MODELS)
