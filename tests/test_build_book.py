from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import build_book


class BuildBookTests(unittest.TestCase):
    def test_builds_sources_in_manifest_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "book").mkdir()
            (root / "book" / "a.md").write_text("# 第一页", encoding="utf-8")
            (root / "book" / "b.md").write_text("# 第二页", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "测试书",
                        "subtitle": "测试副标题",
                        "source_order": [
                            {"id": "a", "path": "book/a.md"},
                            {"id": "b", "path": "book/b.md"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output = root / "build" / "book.md"

            with patch.object(build_book, "ROOT", root):
                result = build_book.build_book(manifest, output)

            content = output.read_text(encoding="utf-8")
            self.assertLess(content.index("# 第一页"), content.index("# 第二页"))
            self.assertEqual(result["sources"], 2)

    def test_rejects_missing_local_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "chapter.md"
            source.write_text("![图](missing.png)", encoding="utf-8")

            with patch.object(build_book, "ROOT", root):
                with self.assertRaises(FileNotFoundError):
                    build_book.validate_images(source.read_text(encoding="utf-8"), source)


if __name__ == "__main__":
    unittest.main()
