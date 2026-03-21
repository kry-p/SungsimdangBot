import threading

from modules.database import Setting


class Settings:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, module_path, key, default=None):
        row = Setting.get_or_none((Setting.module_path == module_path) & (Setting.key == key))
        if row is None:
            return default
        return row.value

    def set(self, module_path, key, value):
        Setting.replace(module_path=module_path, key=key, value=value).execute()
