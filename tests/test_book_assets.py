from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "book" / "chapters"
IMAGE_RE = re.compile(r"!\[([^\]]+)]\(([^)]+)\)")


JPEG_START_OF_FRAME_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def read_jpeg_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError(f"不是有效 JPEG：{path}")

    index = 2
    while index + 8 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        marker = data[index]
        index += 1
        if marker in {0x01, 0xD8, 0xD9}:
            continue
        segment_length = int.from_bytes(data[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            raise ValueError(f"JPEG 数据损坏：{path}")
        if marker in JPEG_START_OF_FRAME_MARKERS:
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += segment_length
    raise ValueError(f"JPEG 缺少尺寸信息：{path}")


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
        images = sorted((ROOT / "book" / "assets" / "illustrations" / "epub").glob("*.jpg"))
        self.assertGreater(len(images), 0, "缺少 EPUB 插画")
        for image in images:
            width, height = read_jpeg_size(image)
            self.assertGreaterEqual(width, 2000, f"图片宽度不足：{image} ({width}×{height})")


if __name__ == "__main__":
    unittest.main()
