from __future__ import annotations

import argparse
import html
import math
import re
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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output" / "pdf"
DEFAULT_PREVIEW_DIR = ROOT / "tmp" / "pdfs"


def register_fonts() -> tuple[str, str]:
    candidates = [
        Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    bold_candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]

    regular = None
    for path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CJK", str(path)))
                regular = "CJK"
                break
            except Exception:
                continue
    if regular is None:
        regular = "Helvetica"

    bold = regular
    for path in bold_candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CJK-Bold", str(path)))
                bold = "CJK-Bold"
                break
            except Exception:
                continue
    return regular, bold


FONT, FONT_BOLD = register_fonts()


def make_styles():
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "CJKBase",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=10.5,
        leading=17,
        textColor=colors.HexColor("#202124"),
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    return {
        "base": base,
        "h1": ParagraphStyle(
            "H1",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=24,
            leading=32,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#10233f"),
            spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=15,
            leading=22,
            textColor=colors.HexColor("#14345f"),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=12.5,
            leading=18,
            textColor=colors.HexColor("#31506f"),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "card_title": ParagraphStyle(
            "CardTitle",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#12395c"),
            spaceAfter=3,
        ),
        "card_text": ParagraphStyle(
            "CardText",
            parent=base,
            fontSize=9,
            leading=13,
            spaceAfter=2,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base,
            leftIndent=12,
            borderColor=colors.HexColor("#c7d4e2"),
            borderWidth=1,
            borderPadding=6,
            backColor=colors.HexColor("#f7f9fb"),
        ),
    }


STYLES = make_styles()


def linkify(text: str) -> str:
    code_spans: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        code_spans.append(match.group(1))
        return f"@@CODE{len(code_spans) - 1}@@"

    text = re.sub(r"`([^`]+)`", save_code, text)
    text = html.escape(text)

    def repl(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{html.escape(url, quote=True)}" color="#175199"><u>{label}</u></a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    for idx, code in enumerate(code_spans):
        safe = html.escape(code)
        text = text.replace(
            f"@@CODE{idx}@@",
            f'<font name="{FONT}" backColor="#eef2f5"> {safe} </font>',
        )
    return text


def paragraph(text: str, style: str = "base") -> Paragraph:
    return Paragraph(linkify(text), STYLES[style])


def split_table_row(line: str) -> list[str]:
    line = line.strip().strip("|")
    return [cell.strip() for cell in line.split("|")]


def table_rows_to_cards(rows: list[list[str]]) -> list:
    story: list = []
    if len(rows) <= 2:
        return story

    headers = rows[0]
    for row in rows[2:]:
        if not any(cell.strip() for cell in row):
            continue
        while len(row) < len(headers):
            row.append("")

        title_bits = [cell for cell in row[:3] if cell]
        title = " · ".join(title_bits) if title_bits else row[0]
        details = []
        for header, cell in zip(headers[3:], row[3:]):
            if cell:
                details.append((header or "说明", cell))
        if not details and len(row) > 1:
            details = [(headers[i] if i < len(headers) else "说明", cell) for i, cell in enumerate(row[1:], 1) if cell]

        data = [[Paragraph(linkify(title), STYLES["card_title"])]]
        for label, value in details:
            data.append([Paragraph(f"<b>{linkify(label)}：</b>{linkify(value)}", STYLES["card_text"])])

        card = Table(data, colWidths=[16.2 * cm], hAlign="LEFT")
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e3")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(KeepTogether([card, Spacer(1, 6)]))
    return story


def parse_markdown(md: str) -> list:
    story: list = []
    lines = md.splitlines()
    i = 0
    pending_list: list[str] = []

    def flush_list():
        nonlocal pending_list
        if not pending_list:
            return
        items = [ListItem(paragraph(item), leftIndent=8) for item in pending_list]
        story.append(
            ListFlowable(
                items,
                bulletType="bullet",
                start="circle",
                leftIndent=18,
                bulletFontName=FONT,
                bulletFontSize=7,
            )
        )
        pending_list = []

    while i < len(lines):
        stripped = lines[i].rstrip().strip()
        if not stripped:
            flush_list()
            story.append(Spacer(1, 4))
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|---"):
            flush_list()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = [split_table_row(row) for row in table_lines]
            story.extend(table_rows_to_cards(rows))
            continue

        if stripped.startswith("# "):
            flush_list()
            story.append(Paragraph(linkify(stripped[2:]), STYLES["h1"]))
            story.append(HRFlowable(width="100%", color=colors.HexColor("#d0d7de"), thickness=1))
            story.append(Spacer(1, 12))
        elif stripped.startswith("## "):
            flush_list()
            story.append(Paragraph(linkify(stripped[3:]), STYLES["h2"]))
        elif stripped.startswith("### "):
            flush_list()
            story.append(Paragraph(linkify(stripped[4:]), STYLES["h3"]))
        elif stripped.startswith("- "):
            pending_list.append(stripped[2:])
        elif re.match(r"^\d+\.\s+", stripped):
            flush_list()
            story.append(paragraph(stripped))
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
        self.text = text

    def __call__(self, canvas, doc):
        width, _height = A4
        canvas.saveState()
        canvas.setFont(FONT, 8)
        canvas.setFillColor(colors.HexColor("#7a8693"))
        canvas.drawString(2.0 * cm, 1.15 * cm, self.text[:70])
        canvas.drawRightString(width - 2.0 * cm, 1.15 * cm, f"第 {doc.page} 页")
        canvas.restoreState()


def default_title(md: str, input_path: Path) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
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
        rightMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
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
    parser = argparse.ArgumentParser(description="Render a Chinese-friendly Markdown report to a polished PDF.")
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
