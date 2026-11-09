"""Convert simple Markdown to Outlook-safe HTML (only tags the M365 draft allowlist accepts).

Usage: python3 agent/md_to_html.py input.md > output.html
Supports: headings, paragraphs, **bold**, *italic*, - bullets, 1. numbers, | tables |, ---.
"""
import html
import re
import sys


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)


def convert(md):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                r = lines[i].strip()
                if not re.fullmatch(r"\|?[\s:|-]+\|?", r):
                    rows.append([c.strip() for c in r.strip("|").split("|")])
                i += 1
            body = []
            for n, row in enumerate(rows):
                tag = "th" if n == 0 and any(row) else "td"
                body.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in row) + "</tr>")
            out.append("<table>" + "".join(body) + "</table>")
            continue
        for marker, tag in (("- ", "ul"), ("1. ", "ol")):
            pattern = r"^[-*]\s" if tag == "ul" else r"^\d+\.\s"
            if re.match(pattern, s):
                items = []
                while i < len(lines) and re.match(pattern, lines[i].strip()):
                    items.append(f"<li>{inline(re.sub(pattern, '', lines[i].strip()))}</li>")
                    i += 1
                out.append(f"<{tag}>{''.join(items)}</{tag}>")
                break
        else:
            if s == "---":
                out.append("<hr>")
            elif s.startswith("### "):
                out.append(f"<h3>{inline(s[4:])}</h3>")
            elif s.startswith("## "):
                out.append(f"<h2>{inline(s[3:])}</h2>")
            elif s.startswith("# "):
                out.append(f"<h1>{inline(s[2:])}</h1>")
            else:
                out.append(f"<p>{inline(s)}</p>")
            i += 1
    return "\n".join(out)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(convert(fh.read()))
