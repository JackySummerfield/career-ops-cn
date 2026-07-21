"""Render the interview-prep Markdown subset as a standalone HTML document.

The renderer intentionally uses only the Python standard library. It covers
the headings, lists, tables, quotes, code blocks, links, and inline emphasis
used by career-ops-cn interview materials.
"""

import argparse
import html
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


FENCE_RE = re.compile(r"^\s*```(?:\s*(.*))?$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LIST_RE = re.compile(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$")
HR_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
INLINE_RE = re.compile(
    r"`([^`\n]+)`"
    r"|\[([^\]\n]+)\]\(([^)\n]+)\)"
    r"|\*\*([^*\n]+)\*\*"
    r"|__([^_\n]+)__"
    r"|(?<!\*)\*([^*\n]+)\*"
    r"|(?<!_)_([^_\n]+)_"
)

CSS = """\
:root {
  --ink: #1d2939;
  --muted: #667085;
  --paper: #fffdf8;
  --canvas: #edf2f0;
  --line: #d9e2df;
  --accent: #0f766e;
  --accent-soft: #e4f3ef;
  --warm: #c2410c;
  --warm-soft: #fff0e6;
  --shadow: 0 18px 50px rgba(29, 41, 57, 0.12);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background: var(--canvas);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.7;
}
a { color: var(--accent); }
.page {
  width: min(100% - 32px, 980px);
  margin: 28px auto;
  overflow: hidden;
  background: var(--paper);
  border: 1px solid rgba(217, 226, 223, 0.9);
  border-radius: 14px;
  box-shadow: var(--shadow);
}
.hero {
  padding: 42px 52px 34px;
  background: linear-gradient(135deg, #f1f8f5 0%, #fffdf8 62%, #fff2e9 100%);
  border-bottom: 1px solid var(--line);
}
.eyebrow {
  margin: 0 0 10px;
  color: var(--warm);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.hero h1 {
  margin: 0;
    font-size: 2.6rem;
  line-height: 1.15;
}
.generated {
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 0.9rem;
}
.toc {
  margin: 26px 52px 0;
  padding: 18px 22px;
  background: var(--accent-soft);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
}
.toc strong { color: var(--accent); }
.toc ul { margin: 8px 0 0; padding-left: 22px; }
.toc li { margin: 2px 0; }
.toc .toc-level-3 { margin-left: 18px; font-size: 0.94em; }
.content { padding: 34px 52px 48px; }
.content h1 { margin-top: 0; font-size: 1.8rem; }
.content h2 {
  margin: 34px 0 14px;
  padding-left: 14px;
  border-left: 4px solid var(--accent);
  font-size: 1.45rem;
  line-height: 1.3;
}
.content h3 {
  margin: 26px 0 10px;
  color: #344054;
  font-size: 1.15rem;
}
.content h4, .content h5, .content h6 { color: #475467; }
.content p { margin: 12px 0; }
.content ul, .content ol { padding-left: 26px; }
.content li { margin: 5px 0; }
.content li > ul, .content li > ol { margin: 4px 0; }
.content input[type="checkbox"] { margin-right: 7px; accent-color: var(--accent); }
blockquote {
  margin: 18px 0;
  padding: 14px 18px;
  color: #475467;
  background: var(--warm-soft);
  border-left: 4px solid var(--warm);
  border-radius: 0 8px 8px 0;
}
code {
  padding: 0.12em 0.35em;
  color: #9a3412;
  background: #fff0e6;
  border-radius: 4px;
  font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
  font-size: 0.9em;
}
pre {
  overflow-x: auto;
  margin: 18px 0;
  padding: 16px 18px;
  color: #e5e7eb;
  background: #25313c;
  border-radius: 8px;
}
pre code { padding: 0; color: inherit; background: transparent; }
hr { margin: 30px 0; border: 0; border-top: 1px solid var(--line); }
table {
  width: 100%;
  margin: 18px 0 24px;
  border-collapse: collapse;
  font-size: 0.94rem;
}
th, td {
  padding: 10px 12px;
  border: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
th { color: #344054; background: #f1f8f5; font-weight: 700; }
tr:nth-child(even) td { background: #fffcf6; }
footer {
  padding: 20px 52px 28px;
  color: var(--muted);
  border-top: 1px solid var(--line);
  font-size: 0.82rem;
}
@media (max-width: 680px) {
  .page { width: 100%; margin: 0; border: 0; border-radius: 0; }
  .hero { padding: 30px 22px 24px; }
    .hero h1 { font-size: 2rem; }
  .toc { margin: 20px 22px 0; }
  .content { padding: 24px 22px 34px; }
  footer { padding: 18px 22px 24px; }
  table { display: block; overflow-x: auto; white-space: nowrap; }
  th, td { min-width: 120px; }
}
"""


def safe_href(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme.lower() in {"http", "https", "mailto"}:
        return value
    if parsed.scheme:
        return "#"
    return value


def render_inline(text: str) -> str:
    parts = []
    cursor = 0
    for match in INLINE_RE.finditer(text):
        parts.append(html.escape(text[cursor : match.start()]))
        if match.group(1) is not None:
            parts.append(f"<code>{html.escape(match.group(1))}</code>")
        elif match.group(2) is not None:
            label = html.escape(match.group(2))
            target = safe_href(match.group(3).split(None, 1)[0])
            parts.append(f'<a href="{html.escape(target, quote=True)}">{label}</a>')
        elif match.group(4) is not None or match.group(5) is not None:
            parts.append(f"<strong>{html.escape(match.group(4) or match.group(5))}</strong>")
        else:
            parts.append(f"<em>{html.escape(match.group(6) or match.group(7))}</em>")
        cursor = match.end()
    parts.append(html.escape(text[cursor:]))
    return "".join(parts)


def plain_text(text: str) -> str:
    text = re.sub(r"!?(\[[^\]]+\])\([^)]+\)", r"\1", text)
    return re.sub(r"[`*_]", "", text).strip()


def heading_id(text: str, used_ids: set[str]) -> str:
    base = re.sub(r"[^\w\s-]", "", plain_text(text), flags=re.UNICODE).strip().lower()
    base = re.sub(r"[\s_]+", "-", base) or "section"
    candidate = base
    suffix = 2
    while candidate in used_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used_ids.add(candidate)
    return candidate


def split_table_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]

    cells = []
    current = []
    escaped = False
    for character in text:
        if character == "|" and not escaped:
            cells.append("".join(current).replace("\\|", "|").strip())
            current = []
            continue
        current.append(character)
        escaped = character == "\\" and not escaped
        if character != "\\":
            escaped = False
    cells.append("".join(current).replace("\\|", "|").strip())
    return cells


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_table(header_line: str, rows: list[str]) -> str:
    headers = split_table_row(header_line)
    body_rows = [split_table_row(row) for row in rows]
    output = ["<div class=\"table-wrap\"><table>", "<thead><tr>"]
    output.extend(f"<th>{render_inline(cell)}</th>" for cell in headers)
    output.append("</tr></thead><tbody>")
    for cells in body_rows:
        output.append("<tr>")
        for index in range(len(headers)):
            cell = cells[index] if index < len(cells) else ""
            output.append(f"<td>{render_inline(cell)}</td>")
        output.append("</tr>")
    output.extend(["</tbody></table></div>"])
    return "".join(output)


def render_list(lines: list[str]) -> str:
    output = []
    stack: list[tuple[int, str]] = []
    for line in lines:
        match = LIST_RE.match(line)
        if not match:
            if output:
                output.append(f"<br>{render_inline(line.strip())}")
            continue

        indent = len(match.group(1).replace("\t", "    "))
        marker = match.group(2)
        tag = "ol" if marker[0].isdigit() else "ul"
        while stack and indent < stack[-1][0]:
            output.append(f"</li></{stack.pop()[1]}>")
        if not stack:
            output.append(f"<{tag}>")
            stack.append((indent, tag))
        elif indent > stack[-1][0]:
            output.append(f"<{tag}>")
            stack.append((indent, tag))
        elif tag != stack[-1][1]:
            output.append(f"</li></{stack.pop()[1]}>")
            output.append(f"<{tag}>")
            stack.append((indent, tag))
        else:
            output.append("</li>")

        content = match.group(3)
        checkbox = re.match(r"\[([ xX])\]\s+(.*)$", content)
        if checkbox:
            checked = " checked" if checkbox.group(1).lower() == "x" else ""
            content_html = f'<input type="checkbox" disabled{checked}>{render_inline(checkbox.group(2))}'
        else:
            content_html = render_inline(content)
        output.append(f"<li>{content_html}")

    while stack:
        output.append(f"</li></{stack.pop()[1]}>")
    return "".join(output)


def is_block_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    if not line.strip():
        return True
    if FENCE_RE.match(line) or HEADING_RE.match(line) or LIST_RE.match(line):
        return True
    if line.lstrip().startswith(">") or HR_RE.match(line):
        return True
    return index + 1 < len(lines) and lines[index + 1].strip() and is_table_separator(lines[index + 1])


def render_document(markdown_text: str, skip_first_h1: bool = False) -> tuple[str, list[tuple[int, str, str]]]:
    lines = markdown_text.replace("\r\n", "\n").split("\n")
    output = []
    headings = []
    used_ids: set[str] = set()
    first_h1_seen = False
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        fence = FENCE_RE.match(line)
        if fence:
            language = (fence.group(1) or "").strip()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            class_name = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            output.append(f"<pre><code{class_name}>{html.escape(chr(10).join(code_lines))}</code></pre>")
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            anchor = heading_id(title, used_ids)
            headings.append((level, anchor, plain_text(title)))
            if not (skip_first_h1 and level == 1 and not first_h1_seen):
                output.append(f'<h{level} id="{html.escape(anchor, quote=True)}">{render_inline(title)}</h{level}>')
            if level == 1:
                first_h1_seen = True
            index += 1
            continue

        if HR_RE.match(line):
            output.append("<hr>")
            index += 1
            continue

        if line.lstrip().startswith(">"):
            quote_lines = []
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[index]))
                index += 1
            quote_html, _ = render_document("\n".join(quote_lines))
            output.append(f"<blockquote>{quote_html}</blockquote>")
            continue

        if LIST_RE.match(line):
            list_lines = []
            while index < len(lines):
                if LIST_RE.match(lines[index]):
                    list_lines.append(lines[index])
                    index += 1
                elif lines[index].strip() and (lines[index].startswith(" ") or lines[index].startswith("\t")):
                    list_lines.append(lines[index])
                    index += 1
                else:
                    break
            output.append(render_list(list_lines))
            continue

        if index + 1 < len(lines) and lines[index + 1].strip() and is_table_separator(lines[index + 1]):
            header_line = line
            index += 2
            table_rows = []
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                table_rows.append(lines[index])
                index += 1
            output.append(render_table(header_line, table_rows))
            continue

        paragraph_lines = [line.strip()]
        index += 1
        while index < len(lines) and not is_block_start(lines, index):
            paragraph_lines.append(lines[index].strip())
            index += 1
        paragraph_html = render_inline(" ".join(paragraph_lines))
        output.append(f"<p>{paragraph_html}</p>")

    return "\n".join(output), headings


def extract_title(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 1:
            return plain_text(heading.group(2)) or "Interview Preparation"
    return "Interview Preparation"


def render_markdown_to_html(markdown_text: str, title: str | None = None) -> str:
    document_title = title or extract_title(markdown_text)
    content, headings = render_document(markdown_text, skip_first_h1=True)
    toc_items = [heading for heading in headings if heading[0] in {2, 3}]
    toc = ""
    if toc_items:
        toc_links = []
        for level, anchor, label in toc_items:
            toc_links.append(
                f'<li class="toc-level-{level}"><a href="#{html.escape(anchor, quote=True)}">{html.escape(label)}</a></li>'
            )
        toc = '<nav class="toc" aria-label="Table of contents"><strong>Contents</strong><ul>' + "".join(toc_links) + "</ul></nav>"

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    escaped_title = html.escape(document_title)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{escaped_title}</title>
<style>{CSS}</style>
</head>
<body>
<main class="page">
<header class="hero">
<p class="eyebrow">Interview preparation</p>
<h1>{escaped_title}</h1>
<p class="generated">Generated {generated}</p>
</header>
{toc}
<article class="content">
{content}
</article>
<footer>Rendered locally from Markdown by career-ops-cn. No network requests or runtime service required.</footer>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render interview-prep Markdown as standalone HTML")
    parser.add_argument("input", type=Path, help="Input Markdown file")
    parser.add_argument("--output", type=Path, default=None, help="Output HTML path (default: input with .html suffix)")
    parser.add_argument("--title", default=None, help="Override the HTML document title")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"ERROR: Markdown file not found: {args.input}", file=sys.stderr)
        return 1

    output = args.output or args.input.with_suffix(".html")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_to_html(args.input.read_text(encoding="utf-8"), args.title), encoding="utf-8")
    print(f"HTML generated: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())