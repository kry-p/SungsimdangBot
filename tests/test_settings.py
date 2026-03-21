import threading

from modules.settings import Settings


class TestSingleton:
    def test_same_instance(self):
        s1 = Settings()
        s2 = Settings()
        assert s1 is s2


class TestGetSet:
    def test_get_default(self):
        s = Settings()
        assert s.get("modules.gemini_chat", "model", "default") == "default"

    def test_set_and_get(self):
        s = Settings()
        s.set("modules.gemini_chat", "model", "gemini-2.5-pro")
        assert s.get("modules.gemini_chat", "model") == "gemini-2.5-pro"

    def test_get_nonexistent_path(self):
        s = Settings()
        assert s.get("modules.nonexistent", "key") is None

    def test_set_preserves_existing(self):
        s = Settings()
        s.set("modules.other", "key", "value")
        s.set("modules.gemini_chat", "model", "gemini-2.5-flash")
        assert s.get("modules.other", "key") == "value"
        assert s.get("modules.gemini_chat", "model") == "gemini-2.5-flash"

    def test_deep_nested_path(self):
        s = Settings()
        s.set("a.b.c.d", "key", "deep_value")
        assert s.get("a.b.c.d", "key") == "deep_value"


class TestThreadSafety:
    def test_concurrent_singleton_creation(self):
        instances = []

        def create():
            instances.append(Settings())

        threads = [threading.Thread(target=create) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(inst is instances[0] for inst in instances)

    def test_concurrent_set_and_get(self):
        s = Settings()
        errors = []

        def setter(i):
            try:
                s.set("modules.test", "key", str(i))
            except Exception as e:
                errors.append(e)

        def getter():
            try:
                s.get("modules.test", "key", None)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=setter, args=(i,)) for i in range(10)]
        threads += [threading.Thread(target=getter) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert s.get("modules.test", "key") is not None
