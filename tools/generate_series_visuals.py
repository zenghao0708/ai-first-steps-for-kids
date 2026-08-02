from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CHARACTER_SHEET = ROOT / "series" / "characters" / "characters.png"
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
)

COLORS = {
    "ink": "#17324d",
    "muted": "#557086",
    "blue": "#5ab8e6",
    "blue_light": "#eaf6fc",
    "yellow": "#f6c453",
    "yellow_light": "#fff6d8",
    "red": "#ef6a61",
    "red_light": "#fff0ed",
    "green": "#67b982",
    "green_light": "#edf8f0",
    "line": "#9bb1c2",
    "paper": "#fbfdff",
}

CHARACTER_CROPS = {
    "小问": (26, 30, 228, 392),
    "朵朵": (18, 410, 220, 785),
    "方方": (12, 790, 235, 1050),
}


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
    raise FileNotFoundError("找不到中文字体，请使用 --font 或 BOOK_CJK_FONT 指定字体")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def fit_font(draw: ImageDraw.ImageDraw, text: str, path: Path, size: int, width: int) -> ImageFont.FreeTypeFont:
    while size >= 20:
        candidate = font(path, size)
        box = draw.textbbox((0, 0), text, font=candidate)
        if box[2] - box[0] <= width:
            return candidate
        size -= 2
    return font(path, 20)


def character_sprite(sheet: Image.Image, name: str, height: int) -> Image.Image:
    sprite = sheet.crop(CHARACTER_CROPS[name]).convert("RGBA")
    pixels = sprite.load()
    for y in range(sprite.height):
        for x in range(sprite.width):
            red, green, blue, alpha = pixels[x, y]
            whiteness = min(red, green, blue)
            if whiteness > 247:
                pixels[x, y] = (red, green, blue, 0)
            elif whiteness > 232:
                pixels[x, y] = (red, green, blue, round(alpha * (247 - whiteness) / 15))
    width = round(sprite.width * height / sprite.height)
    return sprite.resize((width, height), Image.Resampling.LANCZOS)


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str = COLORS["blue"],
    width: int = 10,
) -> None:
    draw.line((start, end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 24
    spread = 0.55
    points = [
        end,
        (
            round(end[0] - length * math.cos(angle - spread)),
            round(end[1] - length * math.sin(angle - spread)),
        ),
        (
            round(end[0] - length * math.cos(angle + spread)),
            round(end[1] - length * math.sin(angle + spread)),
        ),
    ]
    draw.polygon(points, fill=color)


def draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font_path: Path,
    fill: str,
    number: int | None = None,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=COLORS["line"], width=4)
    if number is not None:
        center = (x1 + 42, y1 + 42)
        draw.ellipse((center[0] - 24, center[1] - 24, center[0] + 24, center[1] + 24), fill=COLORS["blue"])
        draw.text(center, str(number), font=font(font_path, 30), fill="white", anchor="mm")
    max_width = x2 - x1 - (110 if number is not None else 50)
    label_font = fit_font(draw, text, font_path, 40, max_width)
    text_x = (x1 + x2) // 2 + (28 if number is not None else 0)
    draw.multiline_text(
        (text_x, (y1 + y2) // 2),
        text,
        font=label_font,
        fill=COLORS["ink"],
        anchor="mm",
        align="center",
        spacing=8,
    )


def draw_flow(draw: ImageDraw.ImageDraw, items: list[str], font_path: Path) -> None:
    count = len(items)
    left, right, y1, y2 = 360, 1920, 320, 820
    gap = 70
    width = (right - left - gap * (count - 1)) // count
    fills = [COLORS["blue_light"], COLORS["yellow_light"], COLORS["green_light"], COLORS["red_light"]]
    boxes = []
    for index, item in enumerate(items):
        x1 = left + index * (width + gap)
        box = (x1, y1, x1 + width, y2)
        boxes.append(box)
        draw_card(draw, box, item, font_path, fills[index % len(fills)], index + 1)
    for first, second in zip(boxes, boxes[1:]):
        draw_arrow(draw, (first[2], (first[1] + first[3]) // 2), (second[0], (second[1] + second[3]) // 2))


def draw_compare(draw: ImageDraw.ImageDraw, items: list[str], font_path: Path) -> None:
    if len(items) < 4:
        raise ValueError("compare 至少需要四项：两个列标题和两组内容")
    halves = [items[2::2], items[3::2]]
    columns = [(380, 290, 1100, 1030), (1170, 290, 1890, 1030)]
    fills = [COLORS["blue_light"], COLORS["yellow_light"]]
    for column_index, box in enumerate(columns):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(box, radius=30, fill=fills[column_index], outline=COLORS["line"], width=4)
        draw.text(
            ((x1 + x2) // 2, y1 + 70),
            items[column_index],
            font=fit_font(draw, items[column_index], font_path, 46, x2 - x1 - 50),
            fill=COLORS["ink"],
            anchor="mm",
        )
        for row, text in enumerate(halves[column_index]):
            cy = y1 + 190 + row * 150
            draw.ellipse((x1 + 55, cy - 17, x1 + 89, cy + 17), fill=COLORS["green"] if column_index else COLORS["blue"])
            draw.text((x1 + 115, cy), text, font=fit_font(draw, text, font_path, 34, x2 - x1 - 170), fill=COLORS["ink"], anchor="lm")


def draw_cycle(draw: ImageDraw.ImageDraw, items: list[str], font_path: Path) -> None:
    if len(items) != 4:
        raise ValueError("cycle 必须正好四项")
    boxes = [
        (560, 250, 1030, 470),
        (1270, 500, 1740, 720),
        (970, 860, 1440, 1080),
        (370, 620, 840, 840),
    ]
    fills = [COLORS["blue_light"], COLORS["yellow_light"], COLORS["green_light"], COLORS["red_light"]]
    for index, (item, box) in enumerate(zip(items, boxes, strict=True)):
        draw_card(draw, box, item, font_path, fills[index], index + 1)
    draw_arrow(draw, (boxes[0][2], 420), (boxes[1][0], 560))
    draw_arrow(draw, (boxes[1][0] + 160, boxes[1][3]), (boxes[2][2] - 80, boxes[2][1]))
    draw_arrow(draw, (boxes[2][0], boxes[2][1] + 70), (boxes[3][2], boxes[3][3] - 40))
    draw_arrow(draw, (boxes[3][2] - 30, boxes[3][1]), (boxes[0][0] + 30, boxes[0][3]))


def draw_tree(draw: ImageDraw.ImageDraw, items: list[str], font_path: Path) -> None:
    if len(items) < 3:
        raise ValueError("tree 至少需要根节点和两个分支")
    root = (850, 230, 1450, 430)
    draw_card(draw, root, items[0], font_path, COLORS["blue_light"])
    branch_count = len(items) - 1
    gap = 30
    left, right = 350, 1950
    width = (right - left - gap * (branch_count - 1)) // branch_count
    for index, item in enumerate(items[1:]):
        x1 = left + index * (width + gap)
        box = (x1, 760, x1 + width, 1040)
        draw.line(
            (
                ((root[0] + root[2]) // 2, root[3]),
                ((x1 + x1 + width) // 2, box[1]),
            ),
            fill=COLORS["blue"],
            width=8,
        )
        draw_card(draw, box, item, font_path, COLORS["yellow_light"] if index % 2 == 0 else COLORS["green_light"], index + 1)


def draw_layers(draw: ImageDraw.ImageDraw, items: list[str], font_path: Path) -> None:
    fills = [COLORS["blue_light"], COLORS["yellow_light"], COLORS["green_light"], COLORS["red_light"]]
    for index, item in enumerate(items):
        inset = index * 65
        box = (430 + inset, 250 + index * 190, 1900 - inset, 410 + index * 190)
        draw_card(draw, box, item, font_path, fills[index % len(fills)], index + 1)


def draw_matrix(draw: ImageDraw.ImageDraw, items: list[str], font_path: Path) -> None:
    if len(items) != 6:
        raise ValueError("matrix 需要六项：两个列标题和四个单元格")
    x_values = [430, 1120, 1810]
    y_values = [260, 480, 720, 960]
    for column, title in enumerate(items[:2]):
        draw_card(draw, (x_values[column], y_values[0], x_values[column + 1], y_values[1]), title, font_path, COLORS["blue_light"])
    for row in range(2):
        for column in range(2):
            index = 2 + row * 2 + column
            draw_card(
                draw,
                (x_values[column], y_values[row + 1], x_values[column + 1], y_values[row + 2]),
                items[index],
                font_path,
                COLORS["yellow_light"] if row == 0 else COLORS["green_light"],
            )


DRAWERS = {
    "flow": draw_flow,
    "compare": draw_compare,
    "cycle": draw_cycle,
    "tree": draw_tree,
    "layers": draw_layers,
    "matrix": draw_matrix,
}


def render(entry: dict[str, Any], font_path: Path, sheet: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (2000, 1365), COLORS["paper"])
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((40, 40, 1960, 1325), radius=36, outline="#d7e3ec", width=4, fill="white")

    kind = entry["kind"]
    if kind not in DRAWERS:
        raise ValueError(f"未知知识图类型：{kind}")
    DRAWERS[kind](draw, entry["items"], font_path)

    note = entry.get("note", "")
    if note:
        draw.rounded_rectangle((390, 1150, 1900, 1275), radius=22, fill="#f2f7fa")
        draw.text(
            (1145, 1212),
            note,
            font=fit_font(draw, note, font_path, 32, 1430),
            fill=COLORS["muted"],
            anchor="mm",
        )

    sprite = character_sprite(sheet, entry.get("character", "小问"), 330)
    canvas.paste(sprite, (70, 930), sprite)
    return canvas


def render_cover(manifest: dict[str, Any], font_path: Path, sheet: Image.Image) -> Image.Image:
    grade = int(manifest["grade"])
    accents = {4: "#5ab8e6", 5: "#67b982", 6: "#ef6a61"}
    accent = accents.get(grade, COLORS["blue"])
    canvas = Image.new("RGB", (1600, 2400), accent)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((70, 70, 1530, 2330), radius=70, fill="white")

    draw.text(
        (800, 270),
        manifest["title"],
        font=fit_font(draw, manifest["title"], font_path, 150, 1350),
        fill=COLORS["ink"],
        anchor="mm",
    )
    draw.text(
        (800, 440),
        manifest["subtitle"],
        font=fit_font(draw, manifest["subtitle"], font_path, 52, 1320),
        fill=COLORS["muted"],
        anchor="mm",
    )
    draw.rounded_rectangle((580, 520, 1020, 620), radius=42, fill=accent)
    draw.text(
        (800, 570),
        f"小学 {grade} 年级",
        font=font(font_path, 46),
        fill="white",
        anchor="mm",
    )

    topics = manifest.get("cover_topics", [])
    for index, topic in enumerate(topics[:6]):
        column, row = index % 2, index // 2
        x1 = 180 + column * 650
        y1 = 720 + row * 205
        box = (x1, y1, x1 + 590, y1 + 150)
        fill = COLORS["blue_light"] if column == 0 else COLORS["yellow_light"]
        draw.rounded_rectangle(box, radius=26, fill=fill, outline=COLORS["line"], width=4)
        draw.ellipse((x1 + 35, y1 + 50, x1 + 85, y1 + 100), fill=accent)
        draw.text(
            (x1 + 115, y1 + 75),
            topic,
            font=fit_font(draw, topic, font_path, 39, 440),
            fill=COLORS["ink"],
            anchor="lm",
        )

    sprites = [
        (character_sprite(sheet, "小问", 600), (80, 1650)),
        (character_sprite(sheet, "方方", 520), (570, 1710)),
        (character_sprite(sheet, "朵朵", 610), (1180, 1640)),
    ]
    for sprite, position in sprites:
        canvas.paste(sprite, position, sprite)

    draw.text(
        (800, 2260),
        "AI 小侦探开源课程系列",
        font=font(font_path, 36),
        fill=COLORS["muted"],
        anchor="mm",
    )
    return canvas


def generate(book_root: Path, font_path: Path) -> int:
    visual_path = book_root / "assets" / "illustrations" / "visuals.json"
    entries = json.loads(visual_path.read_text(encoding="utf-8"))
    base_dir = book_root / "assets" / "illustrations" / "base"
    base_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(CHARACTER_SHEET) as source:
        sheet = source.convert("RGB")
    for entry in entries:
        output = base_dir / entry["file"]
        render(entry, font_path, sheet).save(output, "JPEG", quality=94, optimize=True)
        print(f"已生成知识图底图：{output.relative_to(ROOT)}")
    manifest = json.loads((book_root / "book-manifest.json").read_text(encoding="utf-8"))
    cover_path = book_root / manifest.get("cover", "assets/cover/cover.jpg")
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    render_cover(manifest, font_path, sheet).save(cover_path, "JPEG", quality=94, optimize=True)
    print(f"已生成封面：{cover_path.relative_to(ROOT)}")
    return len(entries)


def main() -> None:
    parser = argparse.ArgumentParser(description="生成四至六年级统一风格知识图底图")
    parser.add_argument("--book-root", type=Path, required=True)
    parser.add_argument("--font")
    args = parser.parse_args()
    count = generate(args.book_root.resolve(), find_font(args.font))
    print(f"完成：{count} 幅知识图底图")


if __name__ == "__main__":
    main()
