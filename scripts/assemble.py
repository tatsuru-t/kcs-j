"""分割して訳したファイル（work/ja/parts/NN*.md）を、章ごとの1ファイルにまとめる。

使い方: python3 -I scripts/assemble.py NN [作業ディレクトリ]   （既定: work）
例:     python3 -I scripts/assemble.py 01

- work/ja/parts/ の NN で始まるファイルを名前順に連結する
- 冒頭の「> 元のページ:」の一覧は、英語版（work/en/NN-*.md）からそのまま写す
  （訳文側で一覧を省略・変更していても、原文のページ構成に揃える）
- 訳文の <a id="page-ID"> が英語版と過不足なく一致するかを検査する
"""
import re
import sys
from pathlib import Path

ANCHOR = re.compile(r'<a id="(page-\d+)"></a>')


def source_list(text: str) -> list[str]:
    lines = text.splitlines()
    start = lines.index("> 元のページ:")
    end = start + 1
    while end < len(lines) and lines[end].startswith("> - "):
        end += 1
    return lines[start:end]


def main():
    num = sys.argv[1]
    work = Path(sys.argv[2] if len(sys.argv) > 2 else "work")
    en = next((work / "en").glob(f"{num}-*.md"))
    parts = sorted((work / "ja" / "parts").glob(f"{num}*.md"))
    if not parts:
        sys.exit(f"訳文が無い: work/ja/parts/{num}*.md")
    ja = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in parts) + "\n"

    en_text = en.read_text(encoding="utf-8")
    old, new = source_list(ja), source_list(en_text)
    ja = ja.replace("\n".join(old), "\n".join(new), 1)

    missing = sorted(set(ANCHOR.findall(en_text)) - set(ANCHOR.findall(ja)))
    extra = sorted(set(ANCHOR.findall(ja)) - set(ANCHOR.findall(en_text)))
    if missing or extra:
        sys.exit(f"アンカーが英語版と一致しない: 不足 {missing} / 余分 {extra}")

    out = work / "ja" / en.name
    out.write_text(ja, encoding="utf-8")
    print(f"{out}: {len(ja):,}字（英語版 {len(en_text):,}字）")


if __name__ == "__main__":
    main()
