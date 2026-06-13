from __future__ import annotations

import argparse
import html
import math
import re
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output" / "pdf"
DEFAULT_PREVIEW_DIR = ROOT / "tmp" / "pdfs"

PAGE_WIDTH, _PAGE_HEIGHT = A4
MARGIN_X = 1.8 * cm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_X


def _register_font(name: str, candidates: list[Path]) -> str | None:
    for path in candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
        except Exception:
            continue
    return None


def register_fonts() -> tuple[str, str, str]:
    regular = _register_font(
        "CJK",
        [
            Path(r"C:\Windows\Fonts\NotoSansSC-Regular.ttf"),
            Path(r"C:\Windows\Fonts\NotoSansCJKsc-Regular.otf"),
            Path(r"C:\Windows\Fonts\SourceHanSansSC-Regular.otf"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\Deng.ttf"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
            Path(r"C:\Windows\Fonts\simsun.ttc"),
        ],
    ) or "Helvetica"

    bold = _register_font(
        "CJK-Bold",
        [
            Path(r"C:\Windows\Fonts\NotoSansSC-Bold.ttf"),
            Path(r"C:\Windows\Fonts\NotoSansCJKsc-Bold.otf"),
            Path(r"C:\Windows\Fonts\SourceHanSansSC-Bold.otf"),
            Path(r"C:\Windows\Fonts\msyhbd.ttc"),
            Path(r"C:\Windows\Fonts\Dengb.ttf"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
        ],
    ) or regular

    mono = _register_font(
        "ReportMono",
        [
            Path(r"C:\Windows\Fonts\CascadiaMono.ttf"),
            Path(r"C:\Windows\Fonts\consola.ttf"),
            Path(r"C:\Windows\Fonts\cour.ttf"),
        ],
    ) or "Courier"

    return regular, bold, mono


FONT, FONT_BOLD, FONT_MONO = register_fonts()


def make_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "CJKBase",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=9.7,
        leading=15.0,
        textColor=colors.HexColor("#1f2933"),
        alignment=TA_LEFT,
        spaceAfter=4,
        wordWrap="CJK",
        splitLongWords=1,
    )
    return {
        "base": base,
        "h1": ParagraphStyle(
            "H1",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=19,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=13.2,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=11.0,
            leading=15,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=7.8,
            leading=10.0,
            textColor=colors.HexColor("#111827"),
            wordWrap="CJK",
            splitLongWords=1,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base,
            fontSize=7.4,
            leading=10.3,
            spaceAfter=0,
            wordWrap="CJK",
            splitLongWords=1,
        ),
        "table_key": ParagraphStyle(
            "TableKey",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=7.8,
            leading=10.8,
            textColor=colors.HexColor("#374151"),
            spaceAfter=0,
            wordWrap="CJK",
            splitLongWords=1,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base,
            fontName=FONT_MONO,
            fontSize=7.2,
            leading=9.4,
            textColor=colors.HexColor("#111827"),
            spaceAfter=0,
            wordWrap="LTR",
            splitLongWords=1,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base,
            leftIndent=9,
            borderColor=colors.HexColor("#94a3b8"),
            borderWidth=0,
            borderPadding=0,
            textColor=colors.HexColor("#374151"),
        ),
    }


STYLES = make_styles()


def normalize_text(text: str) -> str:
    return (
        text.replace("\u00a0", " ")
        .replace("\u2011", "-")
        .replace("\u2012", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2212", "-")
    )


def linkify(text: str) -> str:
    text = normalize_text(text)
    code_spans: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        code_spans.append(match.group(1))
        return f"@@CODE{len(code_spans) - 1}@@"

    text = re.sub(r"`([^`]+)`", save_code, text)
    text = html.escape(text)

    def repl(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        safe_url = html.escape(url, quote=True)
        return f'<a href="{safe_url}" color="#1d4ed8"><u>{label}</u></a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    for idx, code in enumerate(code_spans):
        safe = html.escape(normalize_text(code))
        text = text.replace(
            f"@@CODE{idx}@@",
            f'<font name="{FONT_MONO}" color="#111827">{safe}</font>',
        )
    return text


def paragraph(text: str, style: str = "base") -> Paragraph:
    return Paragraph(linkify(text), STYLES[style])


def split_table_row(line: str) -> list[str]:
    line = line.strip().strip("|")
    return [cell.strip() for cell in line.split("|")]


def is_separator_row(row: list[str]) -> bool:
    return all(re.match(r"^:?-{3,}:?$", cell.strip()) for cell in row if cell.strip())


def visual_len(text: str) -> int:
    length = 0
    for char in re.sub(r"<[^>]+>", "", text):
        length += 2 if ord(char) > 127 else 1
    return length


def table_col_widths(headers: list[str], data_rows: list[list[str]]) -> list[float]:
    col_count = len(headers)
    if col_count <= 0:
        return []

    lowered = [h.strip().lower() for h in headers]
    if col_count == 2:
        first_header = lowered[0]
        first_width = 3.7 * cm if first_header in {"item", "question"} else 4.2 * cm
        return [first_width, CONTENT_WIDTH - first_width]

    if lowered == ["type", "evidence", "strength", "notes"]:
        return [2.2 * cm, 8.2 * cm, 2.0 * cm, CONTENT_WIDTH - 12.4 * cm]

    if lowered[:4] == ["stage", "allowed?", "budget", "notes"]:
        return [5.1 * cm, 2.0 * cm, 3.0 * cm, CONTENT_WIDTH - 10.1 * cm]

    if col_count == 3:
        return [4.2 * cm, 7.8 * cm, CONTENT_WIDTH - 12.0 * cm]

    if col_count == 4:
        weights = [max(visual_len(headers[idx]), 4) for idx in range(col_count)]
        for row in data_rows:
            for idx, cell in enumerate(row[:col_count]):
                weights[idx] = max(weights[idx], min(visual_len(cell), 52))
        total = sum(weights) or 1
        widths = [CONTENT_WIDTH * (weight / total) for weight in weights]
        min_widths = [1.8 * cm, 3.8 * cm, 1.8 * cm, 3.0 * cm]
        for idx, minimum in enumerate(min_widths):
            if widths[idx] < minimum:
                diff = minimum - widths[idx]
                widths[idx] = minimum
                widest = max(range(col_count), key=lambda i: widths[i])
                if widest != idx:
                    widths[widest] = max(widths[widest] - diff, min_widths[widest])
        scale = CONTENT_WIDTH / sum(widths)
        return [width * scale for width in widths]

    return [CONTENT_WIDTH / col_count for _ in range(col_count)]


def table_cell(text: str, style: str) -> Paragraph:
    return Paragraph(linkify(text), STYLES[style])


def markdown_table(rows: list[list[str]]) -> list:
    if len(rows) <= 2:
        return []

    headers = rows[0]
    data_rows = rows[2:] if is_separator_row(rows[1]) else rows[1:]
    col_count = len(headers)
    if col_count == 0:
        return []

    normalized_rows: list[list[str]] = []
    for row in data_rows:
        if not any(cell.strip() for cell in row):
            continue
        row = (row + [""] * col_count)[:col_count]
        normalized_rows.append(row)

    if not normalized_rows:
        return []

    widths = table_col_widths(headers, normalized_rows)
    style_by_col = ["table_key", "table_cell"] if col_count == 2 else ["table_cell"] * col_count
    table_data: list[list[Paragraph]] = [[table_cell(cell, "table_header") for cell in headers]]
    for row in normalized_rows:
        table_data.append([table_cell(cell, style_by_col[min(idx, len(style_by_col) - 1)]) for idx, cell in enumerate(row)])

    table = LongTable(table_data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#cbd5e1")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfdff")]),
            ]
        )
    )
    return [table, Spacer(1, 7)]


def wrapped_code_lines(code: str) -> list[str]:
    lines: list[str] = []
    for raw_line in normalize_text(code).splitlines() or [""]:
        line = raw_line.rstrip()
        if not line:
            lines.append("")
            continue
        indent = len(line) - len(line.lstrip(" "))
        wrapped = textwrap.wrap(
            line,
            width=96,
            subsequent_indent=" " * min(indent + 2, 12),
            break_long_words=True,
            break_on_hyphens=False,
        )
        lines.extend(wrapped or [""])
    return lines


def code_block(code: str) -> list:
    cells = []
    for line in wrapped_code_lines(code):
        safe = html.escape(line).replace(" ", "&nbsp;")
        cells.append(Paragraph(safe or "&nbsp;", STYLES["code"]))

    table = Table([[cells]], colWidths=[CONTENT_WIDTH], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8dee9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [table, Spacer(1, 8)]


def parse_markdown(md: str) -> list:
    story: list = []
    lines = md.splitlines()
    i = 0
    pending_list: list[str] = []
    pending_type: str | None = None

    def flush_list() -> None:
        nonlocal pending_list, pending_type
        if not pending_list:
            return
        bullet_type = "1" if pending_type == "number" else "bullet"
        start = "1" if pending_type == "number" else "circle"
        items = [ListItem(paragraph(item), leftIndent=8) for item in pending_list]
        story.append(
            ListFlowable(
                items,
                bulletType=bullet_type,
                start=start,
                leftIndent=18,
                bulletFontName=FONT,
                bulletFontSize=7,
            )
        )
        story.append(Spacer(1, 2))
        pending_list = []
        pending_type = None

    def add_list_item(kind: str, text: str) -> None:
        nonlocal pending_list, pending_type
        if pending_type and pending_type != kind:
            flush_list()
        pending_type = kind
        pending_list.append(text)

    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()
        if not stripped:
            flush_list()
            story.append(Spacer(1, 3))
            i += 1
            continue

        if stripped.startswith("```"):
            flush_list()
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            story.extend(code_block("\n".join(code_lines)))
            if i < len(lines):
                i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            flush_list()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = [split_table_row(row) for row in table_lines]
            story.extend(markdown_table(rows))
            continue

        if stripped.startswith("# "):
            flush_list()
            story.append(Paragraph(linkify(stripped[2:]), STYLES["h1"]))
            story.append(HRFlowable(width="100%", color=colors.HexColor("#d1d5db"), thickness=0.8))
            story.append(Spacer(1, 9))
        elif stripped.startswith("## "):
            flush_list()
            story.append(Paragraph(linkify(stripped[3:]), STYLES["h2"]))
        elif stripped.startswith("### "):
            flush_list()
            story.append(Paragraph(linkify(stripped[4:]), STYLES["h3"]))
        elif stripped.startswith("- "):
            add_list_item("bullet", stripped[2:])
        elif re.match(r"^\d+\.\s+", stripped):
            add_list_item("number", re.sub(r"^\d+\.\s+", "", stripped))
        elif stripped.startswith(">"):
            flush_list()
            story.append(Paragraph(linkify(stripped.lstrip("> ")), STYLES["quote"]))
        else:
            flush_list()
            story.append(paragraph(stripped))
        i += 1

    flush_list()
    return story


class Footer:
    def __init__(self, text: str):
        self.text = normalize_text(text)

    def __call__(self, canvas, doc):
        width, _height = A4
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN_X, 1.35 * cm, width - MARGIN_X, 1.35 * cm)
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(MARGIN_X, 0.95 * cm, self.text[:74])
        canvas.drawRightString(width - MARGIN_X, 0.95 * cm, f"第 {doc.page} 页")
        canvas.restoreState()


def default_title(md: str, input_path: Path) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return normalize_text(line[2:].strip())
    return input_path.stem.replace("_", " ")


def render_pdf(input_path: Path, output_path: Path | None = None, title: str | None = None, footer: str | None = None) -> Path:
    md = input_path.read_text(encoding="utf-8")
    doc_title = title or default_title(md, input_path)
    doc_footer = footer or doc_title
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / f"{input_path.stem}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=MARGIN_X,
        leftMargin=MARGIN_X,
        topMargin=1.65 * cm,
        bottomMargin=1.65 * cm,
        title=doc_title,
        author="ARIS / Codex",
    )
    doc.build(parse_markdown(md), onFirstPage=Footer(doc_footer), onLaterPages=Footer(doc_footer))
    return output_path


def render_contact_sheet(pdf_path: Path, output_dir: Path | None = None) -> Path:
    try:
        import fitz
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise SystemExit("Preview rendering requires pymupdf and pillow. Install with: python -m pip install pymupdf pillow") from exc

    output_dir = output_dir or DEFAULT_PREVIEW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    thumbs = []
    for idx, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(0.35, 0.35), alpha=False)
        image_path = output_dir / f"{pdf_path.stem}_thumb_{idx + 1}.png"
        pix.save(image_path)
        image = Image.open(image_path).convert("RGB")
        canvas = Image.new("RGB", (image.width, image.height + 26), "white")
        canvas.paste(image, (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, image.height + 6), f"Page {idx + 1}", fill=(40, 40, 40))
        thumbs.append(canvas)

    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    width = max(t.width for t in thumbs)
    height = max(t.height for t in thumbs)
    sheet = Image.new("RGB", (cols * width, rows * height), "white")
    for idx, image in enumerate(thumbs):
        sheet.paste(image, ((idx % cols) * width, (idx // cols) * height))
    sheet_path = output_dir / f"{pdf_path.stem}_contact_sheet.png"
    sheet.save(sheet_path)
    return sheet_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a Chinese-friendly Markdown report to a clean PDF.")
    parser.add_argument("input", type=Path, help="Markdown file to render.")
    parser.add_argument("--output", "-o", type=Path, help="PDF output path. Defaults to output/pdf/<input-stem>.pdf.")
    parser.add_argument("--title", help="PDF metadata/title override. Defaults to first H1.")
    parser.add_argument("--footer", help="Footer text override. Defaults to title.")
    parser.add_argument("--preview", action="store_true", help="Also render a PNG contact sheet to tmp/pdfs/.")
    parser.add_argument("--preview-dir", type=Path, help="Preview output directory. Defaults to tmp/pdfs/.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf = render_pdf(args.input, args.output, args.title, args.footer)
    print(pdf)
    if args.preview:
        print(render_contact_sheet(pdf, args.preview_dir))


if __name__ == "__main__":
    main()
