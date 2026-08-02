from __future__ import annotations

import unittest
from pathlib import Path

from book_cases import book_roots, load_manifest


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = ("漫画开场", "动手试一试", "侦探笔记", "给大人的话")


class ChapterStructureTests(unittest.TestCase):
    def test_chapters_follow_child_reader_structure(self) -> None:
        for book_root in book_roots():
            manifest = load_manifest(book_root)
            chapters = sorted((book_root / "chapters").glob("ch*.md"))
            requirements = manifest.get("chapter_requirements", {})
            minimum_characters = requirements.get("minimum_characters", 2500)
            required_phrases = requirements.get(
                "required_phrases", ["AI 侦探任务", *REQUIRED_SECTIONS]
            )
            self.assertEqual(len(chapters), 12, f"{book_root.name} 应有 12 章正文")
            for chapter in chapters:
                with self.subTest(book=book_root.name, chapter=chapter.name):
                    content = chapter.read_text(encoding="utf-8")
                    self.assertGreaterEqual(
                        len(content), minimum_characters, f"章节内容过短：{chapter}"
                    )
                    for phrase in required_phrases:
                        self.assertIn(phrase, content, f"缺少“{phrase}”：{chapter}")


if __name__ == "__main__":
    unittest.main()
