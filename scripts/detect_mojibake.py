#!/usr/bin/env python3
"""CP949 → UTF-8 mojibake 검출 훅. 잘못된 인코딩으로 저장된 한국어 텍스트가 커밋되는 것을 막는다."""

import re
import sys

# 정상 한국어에서는 거의 발생하지 않는 mojibake 시그니처:
# - "째" + ASCII 알파벳: °C/°F가 깨진 형태
# - "?" 직후 한글: CP949 바이트가 UTF-8로 디코딩될 때 흔한 패턴
PATTERNS = [
    (re.compile(r"째[A-Za-z]"), "단위 깨짐 (°C/°F가 CP949로 깨진 형태)"),
    (re.compile(r"\?[가-힣]"), "물음표 뒤 한글 (CP949 mojibake)"),
    (re.compile(r"\?\?[가-힣]"), "물음표 두 개 뒤 한글 (CP949 mojibake)"),
]


def main(paths: list[str]) -> int:
    failed = False
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue

        for lineno, line in enumerate(lines, start=1):
            for pattern, label in PATTERNS:
                if pattern.search(line):
                    print(f"{path}:{lineno}: {label}: {line.rstrip()}")
                    failed = True

    if failed:
        print("\nmojibake detected. 파일이 CP949/EUC-KR로 저장된 채 커밋되었을 수 있습니다.")
        print("에디터 인코딩을 UTF-8로 다시 저장한 뒤 add → commit 하세요.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
