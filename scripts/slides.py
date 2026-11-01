"""Markdown のスライド原稿（slides/*.md）から、16:9 のHTMLとPDFを作る（個人の学習用）。

使い方: python3 -I scripts/slides.py slides/01-kcs-overview.md [...]
出力:   dist/slides/<名前>.html と dist/slides/<名前>.pdf

外部のスライドツールは使わず、pandoc と Chromium（Playwright）だけで作る。
原稿の書き方:
- スライドは `---` だけの行で区切る。各スライドの最初の `# 見出し` がタイトルになる
- 画像は ../images/ の図をそのまま参照する。画像が1枚と本文があるスライドは、
  画像を右半分に置く。本文の無いスライドは画像を中央に大きく置く
- `<!-- class: title -->` を書いたスライドは表紙の体裁、`<!-- class: small -->` は文字を小さくする
- 文字や画像が枠からはみ出したスライドは、PDFを作るときに番号を表示して知らせる
"""
import html
import re
import subprocess
import sys
from pathlib import Path

CSS = """
@page { size: 1280px 720px; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; background: #e8ebf0; font-family: "Noto Sans CJK JP", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif; }
section { width: 1280px; height: 720px; margin: 24px auto; background: #fff; position: relative;
          padding: 56px 72px 48px; overflow: hidden; page-break-after: always; color: #1f2a37;
          box-shadow: 0 2px 8px rgba(0,0,0,.12); display: flex; flex-direction: column; }
@media print { body { background: #fff; } section { margin: 0; box-shadow: none; } }
section h1 { font-size: 40px; margin: 0 0 24px; color: #0b3c6e; border-left: 10px solid #4cc2d6; padding-left: 18px; line-height: 1.3; }
section .body { flex: 1; display: flex; gap: 40px; min-height: 0; font-size: 25px; line-height: 1.6; }
section .text { flex: 1; min-width: 0; }
section .fig { flex: 1; display: flex; align-items: center; justify-content: center; min-width: 0; }
section .fig img { max-width: 100%; max-height: 100%; object-fit: contain; }
section.figonly .fig { flex: 1; }
section p { margin: 0 0 14px; }
section ul, section ol { margin: 0 0 12px; padding-left: 1.3em; }
section li { margin: 4px 0; }
section li li { font-size: .88em; }
section strong { color: #0b3c6e; }
section table { border-collapse: collapse; font-size: .82em; }
section td, section th { border: 1px solid #c8d0da; padding: 4px 10px; }
section th { background: #eef4fa; }
section blockquote { margin: 0 0 12px; padding: 8px 16px; background: #f3f8fb; border-left: 6px solid #4cc2d6; }
section.small .body { font-size: 21px; }
section.title { justify-content: center; background: linear-gradient(135deg, #0b3c6e, #1f7aa8); color: #fff; }
section.title h1 { color: #fff; border: none; padding: 0; font-size: 52px; }
section.title .body { font-size: 26px; display: block; flex: none; }
section.title strong { color: #fff; }
.pageno { position: absolute; right: 28px; bottom: 16px; font-size: 16px; color: #8a96a3; }
section.title .pageno { color: #cfe3f1; }
.src { position: absolute; left: 72px; bottom: 16px; font-size: 14px; color: #8a96a3; }
section.title .src { color: #cfe3f1; }
"""

OVERFLOW_JS = """
() => [...document.querySelectorAll('section')].map((s, i) => {
  const t = s.querySelector('.text');
  const over = s.scrollHeight > s.clientHeight + 1 || (t && t.scrollHeight > t.clientHeight + 1);
  const broken = [...s.querySelectorAll('img')].some(img => !img.naturalWidth);
  return (over || broken) ? `${i + 1}${broken ? '(画像なし)' : ''}` : null;
}).filter(Boolean)
"""


def md_to_html(md: str) -> str:
    return subprocess.run(["pandoc", "-f", "gfm", "-t", "html5"], input=md,
                          capture_output=True, text=True, check=True).stdout


def render_slide(raw: str, no: int, total: int, footer: str, base: Path) -> str:
    classes = re.findall(r"<!--\s*class:\s*([\w ]+?)\s*-->", raw)
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S).strip()
    m = re.match(r"#\s+(.+)\n?", raw)
    title = m.group(1).strip() if m else ""
    body = raw[m.end():].strip() if m else raw
    images = re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", body)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)\s*", "", body).strip()
    cls = list(classes)
    parts = []
    if text:
        parts.append(f'<div class="text">{md_to_html(text)}</div>')
    if images:
        src = (base / images[0]).resolve().as_uri()
        parts.append(f'<div class="fig"><img src="{src}"></div>')
        if not text:
            cls.append("figonly")
    return (f'<section class="{" ".join(cls)}"><h1>{html.escape(title)}</h1>'
            f'<div class="body">{"".join(parts)}</div>'
            f'<div class="src">{html.escape(footer)}</div>'
            f'<div class="pageno">{no} / {total}</div></section>')


def main():
    out_dir = Path("dist/slides")
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in map(Path, sys.argv[1:]):
        text = src.read_text(encoding="utf-8")
        footer = ""
        fm = re.match(r"<!--\s*footer:\s*(.+?)\s*-->\n", text)
        if fm:
            footer, text = fm.group(1), text[fm.end():]
        slides = [s for s in re.split(r"^---\s*$", text, flags=re.M) if s.strip()]
        doc_title = re.search(r"#\s+(.+)", slides[0]).group(1)
        sections = [render_slide(s, i + 1, len(slides), footer, src.parent) for i, s in enumerate(slides)]
        page = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
                f"<title>{html.escape(doc_title)}</title><style>{CSS}</style></head>"
                f'<body>{"".join(sections)}</body></html>')
        out_html = out_dir / f"{src.stem}.html"
        out_html.write_text(page, encoding="utf-8")
        out_pdf = out_dir / f"{src.stem}.pdf"
        js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch(); const p = await b.newPage({{viewport: {{width: 1280, height: 720}}}});
  await p.goto({str(out_html.resolve().as_uri())!r}); await p.waitForLoadState('networkidle');
  const bad = await p.evaluate({OVERFLOW_JS});
  await p.pdf({{path: {str(out_pdf.resolve())!r}, width: '1280px', height: '720px', printBackground: true}});
  console.log(JSON.stringify(bad)); await b.close();
}})();
"""
        res = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd="/tmp")
        if res.returncode != 0:
            sys.exit(res.stderr)
        bad = res.stdout.strip()
        print(f"{out_pdf}: {len(slides)}枚" + (f"  はみ出し・画像の欠け: {bad}" if bad != "[]" else ""))


if __name__ == "__main__":
    main()
