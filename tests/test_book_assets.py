from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from book_cases import book_roots


ROOT = Path(__file__).resolve().parents[1]
IMAGE_RE = re.compile(r"!\[([^\]]+)]\(([^)]+)\)")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


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
        for book_root in book_roots():
            image_count = 0
            for chapter in sorted((book_root / "chapters").glob("*.md")):
                chapter_images = IMAGE_RE.findall(chapter.read_text(encoding="utf-8"))
                self.assertGreaterEqual(len(chapter_images), 2, f"每章至少需要两幅插画：{chapter}")
                for alt_text, target in chapter_images:
                    image_count += 1
                    self.assertTrue(alt_text.strip(), f"图片缺少替代文本：{chapter}")
                    image = (chapter.parent / target).resolve()
                    self.assertTrue(image.is_file(), f"图片不存在：{image}")
            self.assertGreater(image_count, 0, f"{book_root.name} 尚未引用任何插画")

    def test_epub_images_are_at_least_2000_pixels_wide(self) -> None:
        for book_root in book_roots():
            images = sorted((book_root / "assets" / "illustrations" / "epub").glob("*.jpg"))
            self.assertGreater(len(images), 0, f"{book_root.name} 缺少 EPUB 插画")
            for image in images:
                width, height = read_jpeg_size(image)
                self.assertGreaterEqual(width, 2000, f"图片宽度不足：{image} ({width}×{height})")

    def test_every_chapter_image_has_a_chinese_annotation(self) -> None:
        for book_root in book_roots():
            manifest_path = book_root / "assets" / "illustrations" / "labels.json"
            entries = json.loads(manifest_path.read_text(encoding="utf-8"))
            annotations = {entry["file"]: entry["title"] for entry in entries}

            referenced: set[str] = set()
            for chapter in sorted((book_root / "chapters").glob("*.md")):
                for _, target in IMAGE_RE.findall(chapter.read_text(encoding="utf-8")):
                    referenced.add(Path(target).name)

            self.assertEqual(
                referenced,
                set(annotations),
                f"{book_root.name} 插图中文说明清单与正文引用不一致",
            )
            for filename, title in annotations.items():
                self.assertRegex(title, CHINESE_RE, f"插图说明缺少中文：{filename}")
                base = book_root / "assets" / "illustrations" / "base" / filename
                self.assertTrue(base.is_file(), f"缺少可重复生成的插图底图：{base}")


if __name__ == "__main__":
    unittest.main()
