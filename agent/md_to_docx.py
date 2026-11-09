"""Convert a simple Markdown policy summary into a compact Rosewood-styled .docx.

Usage: python3 agent/md_to_docx.py input.md output.docx [subtitle]
Prints the output size in bytes (pass it as expectedBytes when uploading).

Builds a minimal WordprocessingML package by hand (no template), so the file
stays small enough to upload through the Microsoft 365 connector as base64.
Supports: # / ## / ### headings, paragraphs, **bold**, *italic*, - bullets,
1. numbered items, | tables |, and --- rules.
"""
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape

ORANGE, DARK, GREY = "E86A1F", "1A1A1A", "6B6B6B"
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)
RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)


def run(text, bold=False, italic=False, size=20, color=DARK):
    props = f'<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>{"<w:b/>" if bold else ""}{"<w:i/>" if italic else ""}<w:color w:val="{color}"/><w:sz w:val="{size}"/>'
    return f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
SUBTITLE = "Policy Summary"
LINKS = []  # hyperlink targets collected while building the document


def link(text, url, size=20):
    LINKS.append(url)
    rid = f"rIdL{len(LINKS)}"
    props = f'<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:color w:val="0563C1"/><w:u w:val="single"/><w:sz w:val="{size}"/>'
    return f'<w:hyperlink r:id="{rid}"><w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:hyperlink>'


def runs(text, size=20, color=DARK, bold=False):
    out = []
    pieces = LINK.split(text)
    if len(pieces) > 1:
        for k in range(0, len(pieces), 3):
            out.append(runs(pieces[k], size, color, bold) if pieces[k] else "")
            if k + 2 < len(pieces):
                out.append(link(pieces[k + 1], pieces[k + 2], size))
        return "".join(out)
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            out.append(run(part[2:-2], True, False, size, color))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(run(part[1:-1], bold, True, size, color))
        else:
            out.append(run(part, bold, False, size, color))
    return "".join(out)


def para(inner, before=0, after=80, indent=0):
    ind = f'<w:ind w:left="{indent}" w:hanging="{min(indent, 240)}"/>' if indent else ""
    return f'<w:p><w:pPr><w:spacing w:before="{before}" w:after="{after}"/>{ind}</w:pPr>{inner}</w:p>'


def table(rows):
    rows = [r for r in rows if not re.fullmatch(r"\|?[\s:|-]+\|?", r.strip())]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    width = max(len(r) for r in cells)
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    total = 9638  # A4 width minus margins, in twentieths of a point
    weight = []
    for j in range(width):
        lengths = [len(r[j]) if j < len(r) else 0 for r in cells]
        longest_word = max((len(w) for r in cells if j < len(r) for w in r[j].replace("*", "").split()), default=1)
        weight.append(max(longest_word * 1.6 + 3, min(80, sum(lengths) / len(lengths))))
    cols = [int(total * w / sum(weight)) for w in weight]
    grid = "".join(f'<w:gridCol w:w="{c}"/>' for c in cols)
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
           f'<w:tblBorders>{border}</w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    for i, row in enumerate(cells):
        header = i == 0 and any(row)
        xml.append("<w:tr>")
        for j in range(width):
            text = row[j] if j < len(row) else ""
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="EDEDED"/>' if header else ""
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{cols[j]}" w:type="dxa"/>{shade}</w:tcPr>{para(runs(text, 18, bold=header), after=0)}</w:tc>')
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml) + para("", after=60)


def body_xml(md_text):
    out = [para(run("ROSEWOOD INSURANCE BROKERS", True, size=32), after=0),
           para(run(f"FSP 50431  |  {SUBTITLE}", size=18, color=ORANGE), after=200)]
    lines = md_text.splitlines()
    i, num = 0, 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(table(block))
            continue
        if not re.match(r"^\d+\.\s", s):
            num = 0
        if s == "---":
            out.append(para(run("_" * 70, color=GREY, size=16), after=120))
        elif s.startswith("### "):
            out.append(para(runs(s[4:], 22, bold=True), before=120))
        elif s.startswith("## "):
            out.append(para(runs(s[3:].upper(), 24, ORANGE, True), before=240, after=100))
        elif s.startswith("# "):
            out.append(para(runs(s[2:], 28, bold=True), before=120, after=120))
        elif s.startswith(("- ", "* ")):
            out.append(para(run("•  ") + runs(s[2:]), indent=360))
        elif re.match(r"^\d+\.\s", s):
            num += 1
            out.append(para(run(f"{num}.  ") + runs(re.sub(r"^\d+\.\s", "", s)), indent=360))
        else:
            out.append(para(runs(s)))
        i += 1
    out.append(para(run("Prepared with AI assistance. Checked and approved by a Rosewood representative before use.", italic=True, size=14, color=GREY), before=240))
    sect = '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>'
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>'
            + "".join(out) + sect + "</w:body></w:document>")


def convert(md_text, out_path):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        LINKS.clear()
        z.writestr("word/document.xml", body_xml(md_text))
        rels = "".join(
            f'<Relationship Id="rIdL{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="{escape(u)}" TargetMode="External"/>'
            for i, u in enumerate(LINKS))
        z.writestr("word/_rels/document.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rels + "</Relationships>")


if __name__ == "__main__":
    if len(sys.argv) > 3:
        SUBTITLE = sys.argv[3]
    with open(sys.argv[1], encoding="utf-8") as fh:
        convert(fh.read(), sys.argv[2])
    print(os.path.getsize(sys.argv[2]))
