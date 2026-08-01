from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "book" / "chapters"
REQUIRED_SECTIONS = ("漫画开场", "动手试一试", "侦探笔记", "给大人的话")


class ChapterStructureTests(unittest.TestCase):
    def test_chapters_follow_child_reader_structure(self) -> None:
        chapters = sorted(CHAPTERS.glob("ch*.md"))
        self.assertGreater(len(chapters), 0, "缺少章节正文")
        for chapter in chapters:
            content = chapter.read_text(encoding="utf-8")
            self.assertGreaterEqual(len(content), 2500, f"章节内容过短：{chapter.name}")
            self.assertIn("AI 侦探任务", content, f"缺少侦探任务：{chapter.name}")
            for section in REQUIRED_SECTIONS:
                self.assertIn(section, content, f"缺少“{section}”：{chapter.name}")


if __name__ == "__main__":
    unittest.main()
