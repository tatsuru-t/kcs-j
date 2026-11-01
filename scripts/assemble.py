"""分割して訳したファイル（ja/parts/NN*.md）を、章ごとの1ファイル（ja/NN-slug.md）にまとめる。

使い方: python3 -I scripts/assemble.py NN [別冊のフォルダ]
例:     python3 -I scripts/assemble.py 01        # 本編（en/・ja/）
        python3 -I scripts/assemble.py 01 ai     # AI関連の別冊（ai/en/・ai/ja/）

- ja/parts/ の NN で始まるファイルを名前順に連結する
- 冒頭の「> 元のページ:」の一覧は、英語版（en/NN-*.md）からそのまま写す
  （訳文側で一覧を省略・変更していても、原文のページ構成に揃える）
- 訳文の <a id="page-ID"> が英語版と過不足なく一致するかを検査する
- 見出しの数が英語版と同じかを検査する（訳し漏れた節を見つけるため）
- 図の直後に ja/figures.json の日本語の説明を差し込む
"""
import json
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


IMAGE = re.compile(r"!\[[^\]]*\]\((?:\.\./)+images/([^)\s]+)\)")


def add_captions(text: str) -> str:
    """図を含む段落の直後に、ja/figures.json の日本語の説明を差し込む。

    図の中の文字は英語のままなので、ラベルの訳と図の要点を添える。
    説明を訳文の本体に書き込まないのは、説明だけを後から直せるようにするため。
    同じ段落に同じ図が2回（リンク付きの画像など）出ても、説明は1回だけ付ける。
    """
    captions = json.loads(Path("ja/figures.json").read_text(encoding="utf-8"))
    out = []
    for para in text.split("\n\n"):
        out.append(para)
        names = list(dict.fromkeys(IMAGE.findall(para)))
        for name in names:
            if name not in captions:
                sys.exit(f"図の説明が ja/figures.json に無い: {name}")
            out.append(f"*図：{captions[name]}*")
    return "\n\n".join(out)


def main():
    num = sys.argv[1]
    base = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    en = next((base / "en").glob(f"{num}-*.md"))
    parts = sorted((base / "ja" / "parts").glob(f"{num}*.md"))
    if not parts:
        sys.exit(f"訳文が無い: {base / 'ja' / 'parts'}/{num}*.md")
    ja = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in parts) + "\n"

    en_text = en.read_text(encoding="utf-8")
    old, new = source_list(ja), source_list(en_text)
    ja = ja.replace("\n".join(old), "\n".join(new), 1)

    missing = sorted(set(ANCHOR.findall(en_text)) - set(ANCHOR.findall(ja)))
    extra = sorted(set(ANCHOR.findall(ja)) - set(ANCHOR.findall(en_text)))
    if missing or extra:
        sys.exit(f"アンカーが英語版と一致しない: 不足 {missing} / 余分 {extra}")

    ja = add_captions(ja)

    heading = re.compile(r"^#{1,6} ", re.M)
    n_en, n_ja = len(heading.findall(en_text)), len(heading.findall(ja))
    if n_en != n_ja:
        sys.exit(f"見出しの数が英語版と違う: 英語版 {n_en} / 訳文 {n_ja}")

    out = base / "ja" / en.name
    out.write_text(ja, encoding="utf-8")
    print(f"{out}: {len(ja):,}字（英語版 {len(en_text):,}字）")


if __name__ == "__main__":
    main()
