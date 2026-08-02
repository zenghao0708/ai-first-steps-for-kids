from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

try:
    from tools.build_book import ROOT, build_book
    from tools.build_epub import build_epub, validate_epub
except ModuleNotFoundError:  # Support `python tools/build_series.py` from the repository root.
    from build_book import ROOT, build_book
    from build_epub import build_epub, validate_epub


BOOKS_ROOT = ROOT / "books"
BUILD_ROOT = ROOT / "build"
DIST_ROOT = ROOT / "dist"


def manifests() -> list[Path]:
    paths = sorted(BOOKS_ROOT.glob("grade-*/book-manifest.json"))
    if not paths:
        raise FileNotFoundError("books/grade-* 下没有找到 book-manifest.json")
    return paths


def build_all() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for manifest_path in manifests():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        slug = manifest["slug"]
        markdown_path = BUILD_ROOT / f"{slug}.md"
        epub_path = BUILD_ROOT / f"{slug}.epub"
        book_result = build_book(manifest_path, markdown_path)
        epub_result = build_epub(manifest_path, epub_path)
        validate_result = validate_epub(epub_path)
        results.append(
            {
                "grade": int(manifest["grade"]),
                "title": manifest["title"],
                "slug": slug,
                "markdown": markdown_path,
                "epub": epub_path,
                "characters": book_result["characters"],
                "images": epub_result["images"],
                "entries": validate_result["entries"],
            }
        )
    return results


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def publish(results: list[dict[str, object]]) -> None:
    lines: list[str] = []
    for result in results:
        grade = int(result["grade"])
        source = Path(result["epub"])
        target = DIST_ROOT / f"grade-{grade}" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        lines.append(f"{digest(target)}  {target.relative_to(ROOT).as_posix()}")
        if grade == 3:
            legacy_target = DIST_ROOT / "ai-detective.epub"
            shutil.copyfile(source, legacy_target)
            lines.append(
                f"{digest(legacy_target)}  {legacy_target.relative_to(ROOT).as_posix()}"
            )
    (DIST_ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_dist(results: list[dict[str, object]]) -> None:
    expected_lines: list[str] = []
    for result in results:
        grade = int(result["grade"])
        built = Path(result["epub"])
        published = DIST_ROOT / f"grade-{grade}" / built.name
        if not published.is_file():
            raise FileNotFoundError(f"缺少发布文件：{published.relative_to(ROOT)}")
        if built.read_bytes() != published.read_bytes():
            raise ValueError(f"发布文件不是当前源码构建结果：{published.relative_to(ROOT)}")
        expected_lines.append(
            f"{digest(published)}  {published.relative_to(ROOT).as_posix()}"
        )
        if grade == 3:
            legacy = DIST_ROOT / "ai-detective.epub"
            if not legacy.is_file() or legacy.read_bytes() != built.read_bytes():
                raise ValueError("兼容下载文件 dist/ai-detective.epub 不是当前三年级构建结果")
            expected_lines.append(f"{digest(legacy)}  {legacy.relative_to(ROOT).as_posix()}")
    checksum_path = DIST_ROOT / "SHA256SUMS"
    actual = checksum_path.read_text(encoding="utf-8")
    expected = "\n".join(expected_lines) + "\n"
    if actual != expected:
        raise ValueError("dist/SHA256SUMS 与当前四册发布文件不一致")


def main() -> None:
    parser = argparse.ArgumentParser(description="构建并校验三至六年级全系列电子书")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--publish", action="store_true", help="将构建结果复制到 dist 并更新校验值")
    group.add_argument("--verify-dist", action="store_true", help="验证 dist 与当前源码构建结果完全一致")
    args = parser.parse_args()

    results = build_all()
    if args.publish:
        publish(results)
    elif args.verify_dist:
        verify_dist(results)

    for result in results:
        print(
            f"{result['grade']} 年级《{result['title']}》："
            f"{result['characters']} 字符，{result['images']} 幅图片，"
            f"{result['entries']} 个 EPUB 文件"
        )
    if args.publish:
        print("已更新 dist/grade-3 至 dist/grade-6 和 dist/SHA256SUMS")
    elif args.verify_dist:
        print("dist 发布文件与当前源码构建结果一致")


if __name__ == "__main__":
    main()
