import subprocess

import pytest


def _text_files():
    return (
        subprocess.check_output(["git", "ls-files", "*.py", "*.md", "*.yml", "*.yaml", "*.toml", "*.json", "*.txt"])
        .decode()
        .split()
    )


@pytest.mark.parametrize("path", _text_files())
def test_text_file_is_utf8(path):
    with open(path, encoding="utf-8") as f:
        f.read()
