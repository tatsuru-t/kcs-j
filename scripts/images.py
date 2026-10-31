"""Markdown 中の図をダウンロードして images/ に置き、参照を相対パスに書き換える。

使い方: python3 -I scripts/images.py en ja/parts
        （build.py で en/ を作り直したあとにも実行する。何度実行しても結果は同じ）

- 対象は library.serviceinnovation.org/@api/deki/files/{ID}/{ファイル名} の画像
- 同じ ID は1回だけ取得する（サイズ指定の違う URL も同じ画像として扱う）。
  原寸を取るため、クエリ（size=bestfit など）を外した URL から取る
- 実体は files.mtstatic.com への転送の先にある
- ページの見出し横に出るだけのサムネイル（ファイル名が mindtouch.page#thumbnail）は
  本文の図ではないので、Markdown から取り除く
- 書き換え先は各 Markdown から見た相対パス（en/ と ja/ からは ../images/...、
  ja/parts/ の訳は ja/ に組み上げるので ../images/... のままでよい）
"""
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SITE = "https://library.serviceinnovation.org"
UA = "kcs-j-fetch/1.0 (personal translation)"
IMG_DIR = Path("images")

URL = re.compile(
    r"https://library\.serviceinnovation\.org/@api/deki/files/(\d+)/([^)\s?\"]+)(\?[^)\s\"]*)?")
THUMB = re.compile(r"\[?!\[[^\]]*\]\([^)]*mindtouch\.page%2523thumbnail[^)]*\)\]?(\([^)]*\))?")


def local_name(file_id: str, name: str) -> str:
    """ID とファイル名から、保存するファイル名を作る（拡張子が無ければ付けない）。"""
    name = urllib.parse.unquote(urllib.parse.unquote(name))
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return f"{file_id}-{name}"


def download(file_id: str, name: str, dest: Path) -> None:
    if dest.exists():
        return
    url = f"{SITE}/@api/deki/files/{file_id}/{name}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                dest.write_bytes(res.read())
            print(f"  取得 {dest.name}")
            time.sleep(0.5)
            return
        except Exception as e:
            if attempt == 3:
                raise
            print(f"  再試行 {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 ** (attempt + 1))


def process(md: Path) -> int:
    text = md.read_text(encoding="utf-8")
    text = THUMB.sub("", text)
    count = 0

    def repl(m):
        nonlocal count
        file_id, name = m.group(1), m.group(2)
        dest = IMG_DIR / local_name(file_id, name)
        download(file_id, name, dest)
        count += 1
        return f"../images/{dest.name}"

    new = URL.sub(repl, text)
    if new != md.read_text(encoding="utf-8"):
        md.write_text(new, encoding="utf-8")
    return count


def main():
    IMG_DIR.mkdir(exist_ok=True)
    for d in sys.argv[1:]:
        for md in sorted(Path(d).glob("*.md")):
            n = process(md)
            if n:
                print(f"{md}: {n}か所")


if __name__ == "__main__":
    main()
