from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import tempfile
import unicodedata
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

import mistune

try:
    from tools.build_book import DEFAULT_MANIFEST, ROOT, load_sources, validate_images
except ModuleNotFoundError:  # Support `python tools/build_epub.py` from the repository root.
    from build_book import DEFAULT_MANIFEST, ROOT, load_sources, validate_images


DEFAULT_OUTPUT = ROOT / "build" / "ai-detective.epub"
DEFAULT_COVER = ROOT / "book" / "assets" / "cover" / "cover.jpg"
EPUB_NS = "http://www.idpf.org/2007/ops"
XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"


BOOK_CSS = """
@charset "UTF-8";

:root {
  color: #17243a;
  background: #fff;
  font-family: "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif;
  line-height: 1.75;
}

body {
  margin: 0 auto;
  padding: 4%;
  max-width: 42em;
  word-wrap: break-word;
}

h1, h2, h3 {
  font-family: "Noto Sans CJK SC", "Source Han Sans SC", "PingFang SC", sans-serif;
  line-height: 1.35;
  page-break-after: avoid;
}

h1 {
  color: #16355f;
  font-size: 1.8em;
  border-bottom: 0.15em solid #5ab8e6;
  padding-bottom: 0.35em;
}

h2 {
  color: #205f80;
  margin-top: 1.6em;
}

h3 { color: #28734d; }

p, li { orphans: 2; widows: 2; }

blockquote {
  margin: 1.2em 0;
  padding: 0.7em 1em;
  border-left: 0.35em solid #f06a61;
  background: #fff7e4;
  page-break-inside: avoid;
}

blockquote p { margin: 0.3em 0; }

strong { color: #9e2f2b; }

img {
  display: block;
  width: auto;
  max-width: 100%;
  height: auto;
  margin: 1em auto 0.5em;
  page-break-inside: avoid;
}

em { color: #506174; }

table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.9em;
}

th, td {
  border: 1px solid #aebccc;
  padding: 0.45em;
  vertical-align: top;
}

th { background: #eaf5fb; }

code {
  font-family: "SFMono-Regular", Consolas, monospace;
  background: #f1f4f7;
  padding: 0.1em 0.25em;
}

pre {
  overflow-wrap: break-word;
  white-space: pre-wrap;
  background: #f1f4f7;
  padding: 0.8em;
}

a { color: #166a91; }

.part-label {
  color: #506174;
  font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif;
  font-size: 0.9em;
}

.cover-page { padding: 0; text-align: center; }
.cover-page img { width: 100%; max-height: 100vh; margin: 0 auto; }
""".strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", html.unescape(value)).lower()
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "-", normalized, flags=re.UNICODE)
    return normalized.strip("-") or "section"


class EpubRenderer(mistune.HTMLRenderer):
    def __init__(self, source: Path, source_id: str, image_registry: dict[Path, str]):
        super().__init__(escape=False)
        self.source = source
        self.source_id = source_id
        self.image_registry = image_registry
        self.heading_counts: dict[str, int] = {}
        self.heading_ids: set[str] = set()

    def heading(self, text: str, level: int, **attrs: object) -> str:
        base = slugify(text)
        count = self.heading_counts.get(base, 0) + 1
        self.heading_counts[base] = count
        anchor = f"{self.source_id}-{base}"
        if count > 1:
            anchor = f"{anchor}-{count}"
        self.heading_ids.add(anchor)
        return f'<h{level} id="{html.escape(anchor, quote=True)}">{text}</h{level}>\n'

    def image(self, text: str, url: str, title: str | None = None) -> str:
        if url.startswith(("http://", "https://", "data:")):
            raise ValueError(f"EPUB 不允许远程图片：{url}")
        target = url.split("#", 1)[0]
        image_path = (self.source.parent / target).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"找不到 EPUB 图片：{image_path}")

        filename = self.image_registry.get(image_path)
        if filename is None:
            filename = image_path.name
            used_names = set(self.image_registry.values())
            if filename in used_names:
                digest = hashlib.sha256(str(image_path).encode("utf-8")).hexdigest()[:8]
                filename = f"{image_path.stem}-{digest}{image_path.suffix.lower()}"
            self.image_registry[image_path] = filename

        title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
        return (
            f'<img src="../images/{html.escape(filename, quote=True)}" '
            f'alt="{html.escape(text or "", quote=True)}"{title_attr} />'
        )


def xhtml_document(title: str, body: str, body_type: str, language: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" xml:lang="{html.escape(language)}" lang="{html.escape(language)}">
<head>
  <meta charset="UTF-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/book.css" />
</head>
<body epub:type="{html.escape(body_type, quote=True)}">
{body}
</body>
</html>
'''


def build_nav(items: list[dict], language: str) -> str:
    front = [item for item in items if item["type"] == "front-matter"]
    chapters = [item for item in items if item["type"] == "chapter"]
    back = [item for item in items if item["type"] == "back-matter"]

    lines = ['    <li><a href="cover.xhtml">封面</a></li>']
    for item in front:
        lines.append(
            f'    <li><a href="text/{html.escape(item["id"], quote=True)}.xhtml">{html.escape(item["title"])}</a></li>'
        )

    current_part = None
    for item in chapters:
        part = item.get("part", "正文")
        if part != current_part:
            if current_part is not None:
                lines.extend(["      </ol>", "    </li>"])
            lines.extend([f"    <li><span>{html.escape(part)}</span>", "      <ol>"])
            current_part = part
        lines.append(
            f'        <li><a href="text/{html.escape(item["id"], quote=True)}.xhtml">第 {item["number"]} 章 {html.escape(item["title"])}</a></li>'
        )
    if current_part is not None:
        lines.extend(["      </ol>", "    </li>"])

    if back:
        lines.extend(["    <li><span>附录</span>", "      <ol>"])
        for item in back:
            lines.append(
                f'        <li><a href="text/{html.escape(item["id"], quote=True)}.xhtml">{html.escape(item["title"])}</a></li>'
            )
        lines.extend(["      </ol>", "    </li>"])

    toc = "\n".join(lines)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" xml:lang="{html.escape(language)}" lang="{html.escape(language)}">
<head><meta charset="UTF-8" /><title>目录</title><link rel="stylesheet" type="text/css" href="styles/book.css" /></head>
<body>
  <nav epub:type="toc" id="toc" role="doc-toc">
    <h1>目录</h1>
    <ol>
{toc}
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="hidden">
    <ol>
      <li><a epub:type="cover" href="cover.xhtml">封面</a></li>
      <li><a epub:type="bodymatter" href="text/ch01-ai-around-us.xhtml">正文</a></li>
    </ol>
  </nav>
</body>
</html>
'''


def build_ncx(items: list[dict], uid: str, title: str) -> str:
    nav_items = [("cover", "封面", "cover.xhtml")]
    nav_items.extend((item["id"], item["title"], f'text/{item["id"]}.xhtml') for item in items)
    points = []
    for order, (item_id, label, source) in enumerate(nav_items, start=1):
        points.append(
            f'''    <navPoint id="nav-{html.escape(item_id, quote=True)}" playOrder="{order}">
      <navLabel><text>{html.escape(label)}</text></navLabel>
      <content src="{html.escape(source, quote=True)}" />
    </navPoint>'''
        )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="{NCX_NS}" version="2005-1">
  <head><meta name="dtb:uid" content="{html.escape(uid, quote=True)}" /></head>
  <docTitle><text>{html.escape(title)}</text></docTitle>
  <navMap>
{chr(10).join(points)}
  </navMap>
</ncx>
'''


def media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml"}
    if suffix not in types:
        raise ValueError(f"不支持的图片格式：{path}")
    return types[suffix]


def build_package(manifest: dict, items: list[dict], images: dict[Path, str], uid: str) -> str:
    language = manifest.get("language", "zh-CN")
    creator = manifest.get("creator", "AI 小侦探开源项目")
    modified = manifest.get("modified", "2026-08-01T00:00:00Z")

    manifest_lines = [
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />',
        '    <item id="css" href="styles/book.css" media-type="text/css" />',
        '    <item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml" />',
        '    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image" />',
    ]
    spine_lines = ['    <itemref idref="cover-page" />']
    for item in items:
        item_id = html.escape(item["id"], quote=True)
        manifest_lines.append(
            f'    <item id="{item_id}" href="text/{item_id}.xhtml" media-type="application/xhtml+xml" />'
        )
        spine_lines.append(f'    <itemref idref="{item_id}" />')
    for index, (path, filename) in enumerate(sorted(images.items(), key=lambda pair: pair[1]), start=1):
        manifest_lines.append(
            f'    <item id="image-{index}" href="images/{html.escape(filename, quote=True)}" media-type="{media_type(path)}" />'
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="{OPF_NS}" version="3.0" unique-identifier="book-id" xml:lang="{html.escape(language)}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">
    <dc:identifier id="book-id">{html.escape(uid)}</dc:identifier>
    <dc:title>{html.escape(manifest["title"])}</dc:title>
    <dc:title id="subtitle">{html.escape(manifest.get("subtitle", ""))}</dc:title>
    <meta refines="#subtitle" property="title-type">subtitle</meta>
    <dc:creator>{html.escape(creator)}</dc:creator>
    <dc:language>{html.escape(language)}</dc:language>
    <dc:publisher>{html.escape(manifest.get("publisher", "AI 小侦探开源项目"))}</dc:publisher>
    <dc:rights>{html.escape(manifest.get("rights", "版权与开源许可见仓库说明"))}</dc:rights>
    <meta property="dcterms:modified">{html.escape(modified)}</meta>
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
{chr(10).join(manifest_lines)}
  </manifest>
  <spine toc="ncx">
{chr(10).join(spine_lines)}
  </spine>
</package>
'''


def write_zip_entry(archive: zipfile.ZipFile, name: str, data: str | bytes, compress: bool = True) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data.encode("utf-8") if isinstance(data, str) else data)


def build_epub(manifest_path: Path, output_path: Path, cover_path: Path = DEFAULT_COVER) -> dict[str, int | str]:
    manifest, source_paths = load_sources(manifest_path.resolve())
    items = manifest["source_order"]
    if not cover_path.is_file():
        raise FileNotFoundError(f"找不到封面：{cover_path}")

    image_registry: dict[Path, str] = {}
    documents: dict[str, str] = {}
    for item, source in zip(items, source_paths, strict=True):
        markdown_text = source.read_text(encoding="utf-8")
        validate_images(markdown_text, source)
        renderer = EpubRenderer(source, item["id"], image_registry)
        markdown = mistune.create_markdown(renderer=renderer, plugins=["table"])
        body = markdown(markdown_text)
        if item.get("part"):
            body = f'<p class="part-label">{html.escape(item["part"])}</p>\n' + body
        body_type = "chapter" if item["type"] == "chapter" else item["type"].replace("-", "")
        documents[item["id"]] = xhtml_document(item["title"], body, body_type, manifest["language"])

    uid = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/zenghao0708/ai-first-steps-for-kids')}"
    cover_body = '<div class="cover-page"><img src="images/cover.jpg" alt="AI 小侦探封面" /></div>'
    cover_xhtml = xhtml_document(manifest["title"], cover_body, "cover", manifest["language"]).replace(
        'href="../styles/book.css"', 'href="styles/book.css"'
    )
    container_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="{CONTAINER_NS}" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".epub", dir=output_path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w") as archive:
            write_zip_entry(archive, "mimetype", "application/epub+zip", compress=False)
            write_zip_entry(archive, "META-INF/container.xml", container_xml)
            write_zip_entry(archive, "OEBPS/styles/book.css", BOOK_CSS)
            write_zip_entry(archive, "OEBPS/cover.xhtml", cover_xhtml)
            write_zip_entry(archive, "OEBPS/nav.xhtml", build_nav(items, manifest["language"]))
            write_zip_entry(archive, "OEBPS/toc.ncx", build_ncx(items, uid, manifest["title"]))
            write_zip_entry(archive, "OEBPS/package.opf", build_package(manifest, items, image_registry, uid))
            write_zip_entry(archive, "OEBPS/images/cover.jpg", cover_path.read_bytes())
            for item_id, document in documents.items():
                write_zip_entry(archive, f"OEBPS/text/{item_id}.xhtml", document)
            for image_path, filename in image_registry.items():
                write_zip_entry(archive, f"OEBPS/images/{filename}", image_path.read_bytes())
        temp_path.replace(output_path)
    finally:
        temp_path.unlink(missing_ok=True)

    result = validate_epub(output_path)
    return {
        "sources": len(items),
        "images": len(image_registry) + 1,
        "entries": result["entries"],
        "output": str(output_path),
    }


def validate_epub(epub_path: Path) -> dict[str, int]:
    with zipfile.ZipFile(epub_path) as archive:
        infos = archive.infolist()
        names = {info.filename for info in infos}
        if not infos or infos[0].filename != "mimetype":
            raise ValueError("mimetype 必须是 EPUB 的第一个文件")
        if infos[0].compress_type != zipfile.ZIP_STORED:
            raise ValueError("mimetype 不能压缩")
        if archive.read("mimetype") != b"application/epub+zip":
            raise ValueError("mimetype 内容错误")

        xml_files = [name for name in names if name.endswith((".xml", ".opf", ".ncx", ".xhtml"))]
        roots = {}
        for name in xml_files:
            data = archive.read(name)
            if b"\xef\xbf\xbd" in data:
                raise ValueError(f"发现 Unicode 替换字符：{name}")
            roots[name] = ElementTree.fromstring(data)

        container = roots["META-INF/container.xml"]
        rootfile = container.find(f".//{{{CONTAINER_NS}}}rootfile")
        if rootfile is None:
            raise ValueError("container.xml 缺少 rootfile")
        package_name = rootfile.attrib["full-path"]
        if package_name not in names:
            raise FileNotFoundError(f"EPUB 缺少 package：{package_name}")

        package = roots[package_name]
        for item in package.findall(f".//{{{OPF_NS}}}item"):
            href = item.attrib["href"]
            target = str(PurePosixPath(package_name).parent / href)
            if target not in names:
                raise FileNotFoundError(f"OPF 引用了缺失资源：{target}")

        nav = roots["OEBPS/nav.xhtml"]
        for link in nav.findall(f".//{{{XHTML_NS}}}a"):
            href = link.attrib.get("href", "")
            if href.startswith(("http://", "https://")):
                continue
            path, _, fragment = href.partition("#")
            target = str(PurePosixPath("OEBPS") / path)
            if target not in names:
                raise FileNotFoundError(f"目录链接缺少目标：{target}")
            if fragment:
                ids = {node.attrib["id"] for node in roots[target].iter() if "id" in node.attrib}
                if fragment not in ids:
                    raise ValueError(f"目录锚点不存在：{href}")

    return {"entries": len(infos), "xml_files": len(xml_files)}


def main() -> None:
    parser = argparse.ArgumentParser(description="从书稿 manifest 构建可导航的 EPUB 3 电子书")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cover", type=Path, default=DEFAULT_COVER)
    parser.add_argument("--validate", type=Path, help="只校验指定 EPUB，不重新构建")
    args = parser.parse_args()

    if args.validate:
        result = validate_epub(args.validate)
        print(f"EPUB 校验通过：{args.validate}（{result['entries']} 个文件）")
        return

    result = build_epub(args.manifest, args.output, args.cover)
    print(
        f"已构建 EPUB：{result['sources']} 个源文件，{result['images']} 幅图片，"
        f"{result['entries']} 个包内文件：{result['output']}"
    )


if __name__ == "__main__":
    main()
