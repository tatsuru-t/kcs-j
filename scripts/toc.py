"""訳文の章ファイルから、節（プラクティス・テクニックなど）まで入れた階層付きの目次を作る。

使い方: python3 -I scripts/toc.py --readme   # README.md の目次の部分（目印のコメントの間）を書き換える
        python3 -I scripts/toc.py --html     # HTML版の目次（index.html の元になる Markdown）を出力する

- 本編（ja/）は、各章の <a id="page-ID"> の直後の見出しを節として拾い、2段まで並べる。
  例：03 Solve Loop の下に「プラクティス1：再利用」、その下に「テクニック1.1 …」
- 別冊（ai/ja/）は、元が1ページずつでページのアンカーが無いので、## の見出しを名前だけ並べる
- 見出しの末尾にある英語の括弧書き（例：（Practice 1: Reuse））は目次では省く
- 章の行には、日本語・英語原文へのリンクと、出典欄から読み取ったライセンスを付ける
"""
import re
import sys
from pathlib import Path

ANCHORED = re.compile(r'<a id="(page-\d+)"></a>\s*\n\s*\n(#{2,6}) (.+)')
H2 = re.compile(r"^## (.+)$", re.M)
EN_PAREN = re.compile(r"（[^（）]*[A-Za-z][^（）]*）$")
README_MARKS = {
    "main": ("<!-- toc:main:start -->", "<!-- toc:main:end -->"),
    "ai": ("<!-- toc:ai:start -->", "<!-- toc:ai:end -->"),
}


def label(text: str) -> str:
    """見出しから英語の括弧書きを外す（日本語が残る場合だけ）。"""
    short = EN_PAREN.sub("", text.strip()).strip()
    return short or text.strip()


def license_of(text: str) -> str:
    head = next((l for l in text.splitlines() if l.startswith("> 出典")), "")
    if "ライセンス表示なし" in head:  # 「全体の規定（[CC BY-NC-ND 4.0]）に従うとみなす」と続くので先に見る
        return "表示なし（BY-NC-ND とみなす）"
    m = re.search(r"\[(CC [^\]]+)\]", head)
    if m:
        return m.group(1) + ("（一部ページ）" if "一部ページに表示" in head else "")
    if "クリエイティブ・コモンズの表示なし" in head:
        return "© のみ"
    return ""


def chapter_entries(md: Path):
    """(深さ, 見出し, アンカー or None) の並び。深さは章の中で 0 か 1。"""
    text = md.read_text(encoding="utf-8")
    found = [(len(h), t, a) for a, h, t in ANCHORED.findall(text)]
    if found:
        top = min(level for level, _, _ in found)
        return [(level - top, label(t), a) for level, t, a in found if level - top <= 1]
    return [(0, label(t), None) for t in H2.findall(text)]


def render(book: str, link_ext: str, for_readme: bool) -> str:
    ja_dir, en_dir = (Path("ja"), Path("en")) if book == "main" else (Path("ai/ja"), Path("ai/en"))
    sub = "" if book == "main" else "ai/"
    lines = []
    for md in sorted(ja_dir.glob("[0-9][0-9]-*.md")):
        text = md.read_text(encoding="utf-8")
        title = label(text.splitlines()[0][2:])
        num = md.name[:2]
        if for_readme:
            href = f"{ja_dir.as_posix()}/{md.name}"
            extra = f"（[英語原文]({en_dir.as_posix()}/{md.name})"
            lic = license_of(text)
            extra += f"・{lic}）" if lic else "）"
        else:
            href = f"{sub}{md.stem}{link_ext}"
            extra = ""
        lines.append(f"- {num} [{title}]({href}){extra}")
        for depth, name, anchor in chapter_entries(md):
            indent = "  " * (depth + 1)
            lines.append(f"{indent}- [{name}]({href}#{anchor})" if anchor else f"{indent}- {name}")
    return "\n".join(lines)


def main():
    if "--readme" in sys.argv:
        readme = Path("README.md")
        s = readme.read_text(encoding="utf-8")
        for book, (start, end) in README_MARKS.items():
            i, j = s.index(start) + len(start), s.index(end)
            s = s[:i] + "\n" + render(book, ".md", True) + "\n" + s[j:]
        readme.write_text(s, encoding="utf-8")
        print("README.md の目次を更新した")
    elif "--html" in sys.argv:
        print("# KCS ドキュメント 日本語訳\n\n## 本編（KCS ライブラリ）\n")
        print(render("main", ".html", False))
        print("\n## AI関連（別冊）\n")
        print(render("ai", ".html", False))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
