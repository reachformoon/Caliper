#!/usr/bin/env python
"""Fail if core imports infrastructure or does IO/printing. Run in CI."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "src" / "caliper" / "core"

FORBIDDEN_IMPORTS = ("fastapi", "langgraph", "redis", "psycopg", "sqlite3", "uvicorn", "sqlalchemy")
FORBIDDEN_CALLS = (r"\bprint\s*\(", r"\bsys\.exit\s*\(")
WINDOWS_PATH = re.compile(r"[A-Za-z]:\\")


def main() -> int:
    problems: list[str] = []
    for path in sorted(CORE.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            for mod in FORBIDDEN_IMPORTS:
                if re.search(rf"^\s*(from|import)\s+{mod}\b", code):
                    problems.append(f"{path.relative_to(ROOT)}:{lineno}: forbidden import {mod}")
            for pat in FORBIDDEN_CALLS:
                if re.search(pat, code):
                    problems.append(f"{path.relative_to(ROOT)}:{lineno}: forbidden call {pat}")
            if WINDOWS_PATH.search(code):
                problems.append(f"{path.relative_to(ROOT)}:{lineno}: absolute Windows path")
    if problems:
        print("core purity FAILED:")
        for p in problems:
            print(" -", p)
        return 1
    print("core purity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
