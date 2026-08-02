from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOK_ROOT = ROOT / "books" / "grade-3"

FONT_CANDIDATES = (
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
)


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"插图文字清单为空：{manifest_path}")
    return entries


def find_font(explicit_font: str | None) -> Path:
    candidates: list[Path] = []
    if explicit_font:
        candidates.append(Path(explicit_font).expanduser())
    if os.environ.get("BOOK_CJK_FONT"):
        candidates.append(Path(os.environ["BOOK_CJK_FONT"]).expanduser())
    candidates.extend(FONT_CANDIDATES)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "找不到中文字体。请用 --font 或 BOOK_CJK_FONT 指定支持简体中文的 TTF/TTC 字体。"
    )


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Path,
    initial_size: int,
    max_width: int,
    max_height: int,
) -> ImageFont.FreeTypeFont:
    size = initial_size
    while size >= 14:
        font = ImageFont.truetype(str(font_path), size=size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left <= max_width and bottom - top <= max_height:
            return font
        size -= 2
    raise ValueError(f"文字无法放入指定区域：{text}")


def apply_crop(image: Image.Image, crop: list[float] | None) -> Image.Image:
    if not crop:
        return image
    if len(crop) != 4 or not all(0 <= value <= 1 for value in crop):
        raise ValueError(f"crop 必须是 0 到 1 之间的四个值：{crop}")
    left, top, right, bottom = crop
    if left >= right or top >= bottom:
        raise ValueError(f"crop 边界无效：{crop}")
    return image.crop(
        (
            round(image.width * left),
            round(image.height * top),
            round(image.width * right),
            round(image.height * bottom),
        )
    )


def apply_overlays(
    image: Image.Image,
    overlays: list[dict[str, Any]],
    font_path: Path,
) -> Image.Image:
    if not overlays:
        return image
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for overlay in overlays:
        text = str(overlay["text"])
        center_x = round(annotated.width * float(overlay["x"]))
        center_y = round(annotated.height * float(overlay["y"]))
        max_width = round(annotated.width * float(overlay["max_width"]))
        max_height = round(annotated.height * 0.075)
        initial_size = round(annotated.width * float(overlay.get("font_ratio", 0.03)))
        font = fit_font(draw, text, font_path, initial_size, max_width, max_height)
        draw.text(
            (center_x, center_y),
            text,
            font=font,
            fill="#17324d",
            anchor="mm",
        )
    return annotated


def render_variant(
    source: Image.Image,
    title: str,
    output_size: tuple[int, int],
    font_path: Path,
) -> Image.Image:
    width, height = output_size
    header_height = round(height * 0.09)
    canvas = Image.new("RGB", output_size, "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, header_height), fill="#eef5fa")
    draw.line((0, header_height - 1, width, header_height - 1), fill="#b8cad8", width=2)

    title_font = fit_font(
        draw,
        title,
        font_path,
        initial_size=round(header_height * 0.48),
        max_width=round(width * 0.9),
        max_height=round(header_height * 0.65),
    )
    draw.text(
        (width // 2, header_height // 2),
        title,
        font=title_font,
        fill="#17324d",
        anchor="mm",
    )

    content_size = (width, height - header_height)
    resized = ImageOps.contain(source, content_size, method=Image.Resampling.LANCZOS)
    content_x = (width - resized.width) // 2
    content_y = header_height + (content_size[1] - resized.height) // 2
    canvas.paste(resized, (content_x, content_y))
    return canvas


def bootstrap_base(
    entries: list[dict[str, Any]],
    base_dir: Path,
    print_dir: Path,
    overwrite: bool,
) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        output = base_dir / entry["file"]
        if output.exists() and not overwrite:
            continue
        source = print_dir / Path(entry["file"]).with_suffix(".png")
        if not source.is_file():
            raise FileNotFoundError(f"缺少高清插图源文件：{source}")
        with Image.open(source) as image:
            image.convert("RGB").save(output, "JPEG", quality=95, optimize=True)
        print(f"已建立无说明文字底图：{output.relative_to(ROOT)}")


def annotate(
    entries: list[dict[str, Any]],
    font_path: Path,
    base_dir: Path,
    epub_dir: Path,
    print_dir: Path,
) -> None:
    epub_dir.mkdir(parents=True, exist_ok=True)
    print_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        source_path = base_dir / entry["file"]
        if not source_path.is_file():
            raise FileNotFoundError(
                f"缺少底图：{source_path}。首次运行请先加 --bootstrap-base。"
            )
        with Image.open(source_path) as image:
            source = image.convert("RGB")
        source = apply_crop(source, entry.get("crop"))
        source = apply_overlays(source, entry.get("overlays", []), font_path)

        print_image = render_variant(source, entry["title"], (2400, 1800), font_path)
        print_path = print_dir / Path(entry["file"]).with_suffix(".png")
        print_image.save(print_path, "PNG", optimize=True)

        epub_image = render_variant(source, entry["title"], (2000, 1500), font_path)
        epub_path = epub_dir / entry["file"]
        epub_image.save(epub_path, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"已标注：{epub_path.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为全书插图确定性添加中文说明文字")
    parser.add_argument(
        "--book-root",
        type=Path,
        default=DEFAULT_BOOK_ROOT,
        help="包含 assets/illustrations 的分册目录",
    )
    parser.add_argument("--font", help="支持简体中文的 TTF/TTC 字体路径")
    parser.add_argument(
        "--bootstrap-base",
        action="store_true",
        help="首次运行时从本地高清 print PNG 建立可提交的无标题 JPEG 底图",
    )
    parser.add_argument(
        "--overwrite-base",
        action="store_true",
        help="配合 --bootstrap-base 覆盖现有底图",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asset_root = args.book_root.resolve() / "assets" / "illustrations"
    base_dir = asset_root / "base"
    epub_dir = asset_root / "epub"
    print_dir = asset_root / "print"
    entries = load_manifest(asset_root / "labels.json")
    if args.bootstrap_base:
        bootstrap_base(entries, base_dir, print_dir, overwrite=args.overwrite_base)
    font_path = find_font(args.font)
    annotate(entries, font_path, base_dir, epub_dir, print_dir)
    print(f"完成：{len(entries)} 幅插图，字体 {font_path}")


if __name__ == "__main__":
    main()
