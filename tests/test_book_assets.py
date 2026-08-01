from __future__ import annotations

import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "book" / "chapters"
IMAGE_RE = re.compile(r"!\[([^\]]+)]\(([^)]+)\)")


def read_png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"不是有效 PNG：{path}")
    return struct.unpack(">II", data[16:24])


class BookAssetTests(unittest.TestCase):
    def test_chapter_images_have_alt_text_and_exist(self) -> None:
        image_count = 0
        for chapter in sorted(CHAPTERS.glob("*.md")):
            for alt_text, target in IMAGE_RE.findall(chapter.read_text(encoding="utf-8")):
                image_count += 1
                self.assertTrue(alt_text.strip(), f"图片缺少替代文本：{chapter}")
                image = (chapter.parent / target).resolve()
                self.assertTrue(image.is_file(), f"图片不存在：{image}")
        self.assertGreater(image_count, 0, "书稿尚未引用任何插画")

    def test_epub_images_are_at_least_2000_pixels_wide(self) -> None:
        images = sorted((ROOT / "book" / "assets" / "illustrations" / "epub").glob("*.png"))
        self.assertGreater(len(images), 0, "缺少 EPUB 插画")
        for image in images:
            width, height = read_png_size(image)
            self.assertGreaterEqual(width, 2000, f"图片宽度不足：{image} ({width}×{height})")


if __name__ == "__main__":
    unittest.main()
