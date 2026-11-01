"""訳文と図を1つの zip にまとめる（メールで送って手元で読むため）。

使い方: python3 -I scripts/package.py [--with-en] [--no-html]
出力:   dist/kcs-j-YYYYMMDD.zip

zip に入るもの:
- html/  各章をブラウザで読めるHTMLにしたもの（pandoc。--no-html で省く）
- ja/    訳文の Markdown（ja/parts は入れない）
- images/ 図
- glossary.md、README.md、NOTICE.txt（利用条件の注意）
- en/    英語原文（--with-en を付けたときだけ）

Markdown と HTML のどちらも ../images/ を参照するので、zip を展開した
フォルダの構成のまま開けば図が表示される。
"""
import argparse
import datetime
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

NOTICE = """\
KCS ドキュメント 日本語訳（個人の学習用）

この zip は Consortium for Service Innovation の KCS ライブラリ
（https://library.serviceinnovation.org/KCS）を章ごとにまとめ直し、日本語に訳したものです。

- 原文の著作権は Consortium for Service Innovation にあります。
  KCS® is a service mark of the Consortium for Service Innovation™.
- 一部の文書（原則とコアコンセプト、コーチ・リファレンスガイド、補足資料）は
  CC BY-NC-ND 4.0（改変禁止）です。翻訳・再構成したものを他の人に配布・共有できません。
- 12「AI導入の要点」は serviceinnovation.org のページで、クリエイティブ・コモンズの表示が
  ありません（通常の著作権）。翻訳したものを他の人に配布・共有できません。
- Practices Guide (2027) と Measuring Self-Service Success (2027) は CC BY-NC 4.0 です。
  共有する場合も非営利に限り、出典と変更した旨を示す必要があります。
- 各章のライセンスは README.md の目次の表、各章の冒頭の出典欄にあります。

自分で読むためのものとして扱い、社内での回覧・共有はしないでください。
"""

HTML_STYLE = """\
<style>
body { max-width: 52rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.8;
       font-family: "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif; color: #222; }
img { max-width: 100%; height: auto; border: 1px solid #ddd; }
table { border-collapse: collapse; } td, th { border: 1px solid #ccc; padding: .3rem .5rem; }
blockquote { color: #555; border-left: 4px solid #ccc; margin-left: 0; padding-left: 1rem; }
em { color: #444; }
</style>
"""


def to_html(md: Path, out: Path) -> None:
    """Markdown の章を単独のHTMLにする。章どうしのリンクは .html に付け替える。"""
    text = md.read_text(encoding="utf-8")
    text = re.sub(r"\]\((\d\d-[^)#]+)\.md(#[^)]*)?\)", r"](\1.html\2)", text)
    text = text.replace("](README.md)", "](index.html)")
    title = next((l[2:] for l in text.splitlines() if l.startswith("# ")), md.stem)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as head:
        head.write(HTML_STYLE)
    subprocess.run(
        ["pandoc", "--quiet", "-f", "gfm", "-t", "html5", "--standalone",
         "--metadata", f"title={title}", "--metadata", "lang=ja",
         "--include-in-header", head.name, "-o", str(out)],
        input=text, text=True, check=True)
    Path(head.name).unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-en", action="store_true", help="英語原文も入れる")
    ap.add_argument("--no-html", action="store_true", help="HTML版を作らない")
    args = ap.parse_args()

    chapters = sorted(Path("ja").glob("[0-9][0-9]-*.md"))
    if len(chapters) < 11:
        sys.exit(f"ja/ の章が足りない（{len(chapters)}）。先に assemble.py を実行する")

    Path("dist").mkdir(exist_ok=True)
    name = f"kcs-j-{datetime.date.today():%Y%m%d}"
    zpath = Path("dist") / f"{name}.zip"

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        def add(path: Path, arc: str):
            z.write(path, f"{name}/{arc}")

        z.writestr(f"{name}/NOTICE.txt", NOTICE)
        add(Path("README.md"), "README.md")
        add(Path("glossary.md"), "glossary.md")
        for md in chapters:
            add(md, f"ja/{md.name}")
        for img in sorted(Path("images").iterdir()):
            add(img, f"images/{img.name}")
        if args.with_en:
            for md in sorted(Path("en").glob("*.md")):
                add(md, f"en/{md.name}")
        if not args.no_html:
            with tempfile.TemporaryDirectory() as tmp:
                index = ["# KCS ドキュメント 日本語訳", "", "NOTICE.txt の利用条件も読んでください。", ""]
                for md in chapters:
                    out = Path(tmp) / f"{md.stem}.html"
                    to_html(md, out)
                    add(out, f"html/{out.name}")
                    title = md.read_text(encoding="utf-8").splitlines()[0][2:]
                    index.append(f"- [{title}]({md.stem}.html)")
                idx_md = Path(tmp) / "index.md"
                idx_md.write_text("\n".join(index) + "\n", encoding="utf-8")
                to_html(idx_md, Path(tmp) / "index.html")
                add(Path(tmp) / "index.html", "html/index.html")

    size = zpath.stat().st_size / 1024 / 1024
    print(f"{zpath}（{size:.1f} MB）")
    if size > 10:
        print("注意: 10MB を超えている。メールの添付上限に引っかかるかもしれない", file=sys.stderr)


if __name__ == "__main__":
    main()
