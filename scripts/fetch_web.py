"""serviceinnovation.org（WordPress）の単独ページを、英語版の章ファイルとして取り込む。

使い方: python3 -I scripts/fetch_web.py URL 章ファイル名 "H1の見出し" [出力先のフォルダ]
例:     python3 -I scripts/fetch_web.py https://www.serviceinnovation.org/ai-implementation-essentials/ \\
            01-ai-implementation-essentials "AI Implementation Essentials" ai
出力:   出力先のフォルダ/en/章ファイル名.md（既定は en/）、図は images/web-*.png（本編と共有）

KCSライブラリ（MindTouch）とは別のサイトなので fetch.py / convert.py は使えない。
- 本文は .entry-content だけを取る。冒頭の大見出しの帯（h1 の重複）と、
  最新ブログ記事を自動で並べる「Latest Automation News」の枠は時期で変わるので除く
- ページ内の目次のリンク（#...）は Markdown にするとアンカーが無くなるので、文字だけ残す
- このサイトにはクリエイティブ・コモンズの表示が無い（フッターは © のみ）。
  出典欄にもそう書く
"""
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

UA = "kcs-j-fetch/1.0 (personal translation)"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read()


def main():
    url, name, title = sys.argv[1], sys.argv[2], sys.argv[3]
    out_dir = Path(sys.argv[4] if len(sys.argv) > 4 else ".") / "en"
    img_prefix = os.path.relpath("images", out_dir)  # en/ からは ../images、ai/en/ からは ../../images
    soup = BeautifulSoup(get(url), "html.parser")
    body = soup.select_one(".entry-content")
    if body is None:
        sys.exit("本文（.entry-content）が見つからない")

    for tag in body.find_all(["script", "style", "noscript", "button", "svg"]):  # 拡大ボタンのアイコンなど
        tag.decompose()
    for h in body.find_all("h1"):  # 冒頭の帯に入っている重複した大見出し
        h.decompose()
    for h in body.find_all("h2"):
        if h.get_text(strip=True) == "Latest Automation News":
            box = h.find_parent(class_="wp-block-group") or h
            box.decompose()
    for a in body.find_all("a", href=True):
        if a["href"].startswith("#") or urllib.parse.urlparse(a["href"]).path == urllib.parse.urlparse(url).path and "#" in a["href"]:
            a.unwrap()
        elif a["href"].startswith("/"):
            a["href"] = urllib.parse.urljoin(url, a["href"])

    # 図を取り込む（サイトのロゴのような飾りも含めて、本文中の img はすべて）
    Path("images").mkdir(exist_ok=True)
    for img in body.find_all("img"):
        if img.get("src", "").startswith("data:"):  # 画像の拡大ボタンなどの飾りのアイコン
            img.decompose()
            continue
        src = urllib.parse.urljoin(url, img.get("src", ""))
        base = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(urllib.parse.urlparse(src).path).name)
        dest = Path("images") / f"web-{base}"
        if not dest.exists():
            dest.write_bytes(get(src))
            print(f"  取得 {dest.name}")
            time.sleep(0.5)
        img.attrs = {"src": f"{img_prefix}/{dest.name}", "alt": img.get("alt") or dest.stem}
        if img.parent.name == "a":  # 拡大表示用のリンクも取り込んだ画像に向ける
            img.parent["href"] = img["src"]

    md = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
        input=str(body), capture_output=True, text=True, check=True).stdout
    md = md.replace(" ", " ")
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()

    header = [
        f"# {title}", "",
        f"> 出典: Consortium for Service Innovation, *{title}* — ページにクリエイティブ・コモンズの"
        "表示なし（© Consortium for Service Innovation）  ",
        "> 元のページ:",
        f"> - [{title}]({url})", "", "",
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.md"
    out.write_text("\n".join(header) + md + "\n", encoding="utf-8")
    print(f"{out}: {len(md):,}字")


if __name__ == "__main__":
    main()
