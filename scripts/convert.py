"""取得した本文HTML（work/raw/{id}.xml）をページ単位のMarkdownに変換する。

使い方: python3 -I scripts/convert.py [作業ディレクトリ]   （既定: work）
出力: work/pages/{id}.md

MindTouch固有の装飾（section の div、アンカー用の空 span、style 属性、
ウィジェット）を落としてから pandoc で GitHub 風 Markdown にする。
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SITE = "https://library.serviceinnovation.org"


def flatten_layout_tables(soup: BeautifulSoup) -> None:
    """名前を段組みに並べるだけのレイアウト用の表を箇条書きにする。

    見出しセルが無く、セルの中に段落が複数ある表は、pandoc が Markdown の表に
    できず `[TABLE]` に置き換えてしまう（謝辞のページの名簿がこれだった）。
    セルの段落を左の列から順に取り出して1つの箇条書きにする。
    """
    for table in soup.find_all("table"):
        if table.find("th"):
            continue
        cells = table.find_all("td")
        if not any(len(c.find_all("p")) > 1 for c in cells):
            continue
        ul = soup.new_tag("ul")
        for cell in cells:
            for p in cell.find_all("p") or [cell]:
                text = p.get_text(" ", strip=True)
                if text:
                    li = soup.new_tag("li")
                    li.string = text
                    ul.append(li)
        table.replace_with(ul)


def clean(body: str) -> str:
    soup = BeautifulSoup(body, "html.parser")
    for tag in soup.find_all(["style", "script", "noscript"]):
        tag.decompose()
    flatten_layout_tables(soup)
    # 見出しの前に置かれたアンカー用の空 span
    for span in soup.find_all("span"):
        if not span.get_text(strip=True) and not span.find("img"):
            span.decompose()
    # 装飾だけの入れ物は中身を残して外す
    for tag in soup.find_all(["div", "span", "font", "section"]):
        tag.unwrap()
    for tag in soup.find_all(True):
        keep = {"href", "src", "alt", "colspan", "rowspan"}
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in keep}
        if tag.name == "img" and tag.get("src", "").startswith("/"):
            tag["src"] = SITE + tag["src"]
        if tag.name == "a" and tag.get("href", "").startswith("/"):
            tag["href"] = SITE + tag["href"]
    # 中身の無い段落・強調
    for tag in soup.find_all(["p", "strong", "em", "b", "i"]):
        if not tag.get_text(strip=True) and not tag.find("img"):
            tag.decompose()
    return str(soup)


def to_markdown(fragment: str) -> str:
    out = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
        input=fragment, capture_output=True, text=True, check=True).stdout
    out = out.replace(" ", " ")
    out = re.sub(r"[ \t]+\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def main():
    work = Path(sys.argv[1] if len(sys.argv) > 1 else "work")
    outdir = work / "pages"
    outdir.mkdir(exist_ok=True)
    for p in json.loads((work / "manifest.json").read_text(encoding="utf-8")):
        raw = (work / "raw" / f"{p['id']}.xml").read_text(encoding="utf-8")
        m = re.search(r"<body>(.*?)</body>", raw, re.S)
        body = html.unescape(m.group(1)) if m else ""
        (outdir / f"{p['id']}.md").write_text(to_markdown(clean(body)), encoding="utf-8")


if __name__ == "__main__":
    main()
