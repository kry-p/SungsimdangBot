import json
import os
import shutil
import tempfile
import threading

from modules import log

logger = log.Logger()

SETTINGS_PATH = "data/settings.json"


class Settings:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._data = {}
                cls._instance._load()
        return cls._instance

    def get(self, module_path, key, default=None):
        with self._lock:
            d = self._data
            for part in module_path.split("."):
                if not isinstance(d, dict):
                    return default
                d = d.get(part, {})
            if not isinstance(d, dict):
                return default
            return d.get(key, default)

    def set(self, module_path, key, value):
        with self._lock:
            d = self._data
            for part in module_path.split("."):
                d = d.setdefault(part, {})
            d[key] = value
            self._save()

    def _load(self):
        try:
            with open(SETTINGS_PATH) as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = {}
        except (json.JSONDecodeError, TypeError):
            logger.log_error("Settings JSON corrupted, falling back to empty.")
            shutil.copy2(SETTINGS_PATH, SETTINGS_PATH + ".bak")
            self._data = {}

    def _save(self):
        dir_path = os.path.dirname(SETTINGS_PATH)
        os.makedirs(dir_path, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=dir_path, delete=False, suffix=".tmp") as tmp:
            json.dump(self._data, tmp)
        os.replace(tmp.name, SETTINGS_PATH)
