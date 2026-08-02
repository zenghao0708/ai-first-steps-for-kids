from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def book_roots() -> list[Path]:
    roots = sorted(path for path in (ROOT / "books").glob("grade-*") if (path / "book-manifest.json").is_file())
    if not roots:
        raise AssertionError("books/ 下没有可测试的分册")
    return roots


def load_manifest(book_root: Path) -> dict:
    return json.loads((book_root / "book-manifest.json").read_text(encoding="utf-8"))
