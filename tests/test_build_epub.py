import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_epub import DEFAULT_MANIFEST, build_epub, validate_epub


ROOT = Path(__file__).resolve().parents[1]


class BuildEpubTests(unittest.TestCase):
    def test_builds_valid_epub_with_navigation_and_images(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "book.epub"
            result = build_epub(DEFAULT_MANIFEST, output)
            validation = validate_epub(output)

            self.assertEqual(result["sources"], 18)
            self.assertEqual(result["images"], 28)
            self.assertGreater(validation["entries"], 40)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                nav = archive.read("OEBPS/nav.xhtml").decode("utf-8")
                chapter = archive.read("OEBPS/text/ch10-robots-and-ai.xhtml").decode("utf-8")

            self.assertIn("OEBPS/images/cover.jpg", names)
            self.assertIn("第四站 做负责任的 AI 小创造者", nav)
            self.assertIn("AI 小侦探词典", nav)
            self.assertIn('id="ch10-robots-and-ai-第-10-章-机器人就是-ai-吗"', chapter)
            self.assertIn("感知—决定—行动", chapter)


if __name__ == "__main__":
    unittest.main()
