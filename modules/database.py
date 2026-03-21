import os

from peewee import CharField, FloatField, IntegerField, Model, SqliteDatabase

DB_PATH = os.path.join("data", "bot.db")

db = SqliteDatabase(None)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db.init(DB_PATH, pragmas={"journal_mode": "wal", "foreign_keys": 1})
    db.connect(reuse_if_open=True)
    db.create_tables([Setting, AllowedChat, PendingAction, RouletteGame])


class BaseModel(Model):
    class Meta:
        database = db


class Setting(BaseModel):
    module_path = CharField()
    key = CharField()
    value = CharField()

    class Meta:
        table_name = "settings"
        indexes = ((("module_path", "key"), True),)


class AllowedChat(BaseModel):
    chat_id = IntegerField(unique=True)
    name = CharField(default="")

    class Meta:
        table_name = "allowed_chats"


class PendingAction(BaseModel):
    msg_id = IntegerField(unique=True)
    action = CharField()
    chat_id = IntegerField()
    name = CharField(default="")
    timestamp = FloatField()

    class Meta:
        table_name = "pending_actions"


class RouletteGame(BaseModel):
    chat_id = IntegerField(unique=True)
    bullets = CharField()

    class Meta:
        table_name = "roulette_games"
