import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BackMatterTests(unittest.TestCase):
    def test_manifest_includes_complete_back_matter(self):
        manifest = json.loads((ROOT / "book/book-manifest.json").read_text(encoding="utf-8"))
        back_matter = [item["id"] for item in manifest["source_order"] if item["type"] == "back-matter"]

        self.assertEqual(
            back_matter,
            ["glossary", "task-cards", "adult-guide", "fact-checking"],
        )

    def test_glossary_has_forty_terms(self):
        content = (ROOT / "book/back-matter/01-glossary.md").read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r"^## \d+\. ", content, flags=re.MULTILINE)), 40)

    def test_task_cards_cover_all_chapters(self):
        content = (ROOT / "book/back-matter/02-task-cards.md").read_text(encoding="utf-8")
        card_numbers = re.findall(r"^## 任务卡 (\d+)：", content, flags=re.MULTILINE)

        self.assertEqual(card_numbers, [str(number) for number in range(1, 13)])

    def test_reference_section_uses_direct_links(self):
        content = (ROOT / "book/back-matter/04-fact-checking-and-references.md").read_text(
            encoding="utf-8"
        )

        self.assertGreaterEqual(len(re.findall(r"\]\(https://", content)), 8)


if __name__ == "__main__":
    unittest.main()
