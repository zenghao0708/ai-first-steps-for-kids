from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "book" / "book-manifest.json"
DEFAULT_OUTPUT = ROOT / "build" / "book.md"
IMAGE_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")


def load_sources(manifest_path: Path) -> tuple[dict, list[Path]]:
    repository_root = ROOT.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest.get("source_order")
    if not isinstance(items, list) or not items:
        raise ValueError("source_order 必须是非空列表")

    sources: list[Path] = []
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 个章节配置不是对象")
        item_id = item.get("id")
        relative_path = item.get("path")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"第 {index} 个章节缺少 id")
        if item_id in seen_ids:
            raise ValueError(f"重复章节 id：{item_id}")
        seen_ids.add(item_id)
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError(f"章节 {item_id} 缺少 path")

        source = (repository_root / relative_path).resolve()
        try:
            source.relative_to(repository_root)
        except ValueError as exc:
            raise ValueError(f"章节路径越出仓库：{relative_path}") from exc
        if source in seen_paths:
            raise ValueError(f"重复章节路径：{relative_path}")
        seen_paths.add(source)
        if not source.is_file():
            raise FileNotFoundError(f"找不到章节文件：{relative_path}")
        sources.append(source)
    return manifest, sources


def validate_images(text: str, source: Path) -> None:
    repository_root = ROOT.resolve()
    for match in IMAGE_RE.finditer(text):
        target = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
        if target.startswith(("http://", "https://", "data:")):
            continue
        image_path = (source.parent / target.split("#", 1)[0]).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(
                f"{source.resolve().relative_to(repository_root)} 引用了缺失图片：{target}"
            )


def build_book(manifest_path: Path, output_path: Path) -> dict[str, int | str]:
    repository_root = ROOT.resolve()
    manifest, sources = load_sources(manifest_path.resolve())
    sections = [
        f"# {manifest['title']}",
        "",
        f"## {manifest.get('subtitle', '')}",
        "",
        "<!-- 此文件由 tools/build_book.py 自动生成，请修改各章节源文件。 -->",
        "",
    ]
    for source in sources:
        text = source.read_text(encoding="utf-8").strip()
        validate_images(text, source)
        sections.extend([f"<!-- source: {source.relative_to(repository_root)} -->", text, ""])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(sections).rstrip() + "\n"
    output_path.write_text(content, encoding="utf-8")
    return {"sources": len(sources), "characters": len(content), "output": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="按 manifest 合并并检查少儿 AI 书稿")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_book(args.manifest, args.output)
    print(
        f"已构建 {result['sources']} 个源文件，共 {result['characters']} 个字符：{result['output']}"
    )


if __name__ == "__main__":
    main()
