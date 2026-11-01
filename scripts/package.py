"""訳文と図を1つの zip にまとめる（メールで送って手元で読むため）。

使い方: python3 -I scripts/package.py [--with-en] [--no-html]
出力:   dist/kcs-j-YYYYMMDD.zip（訳文・図・HTML版）
        dist/kcs-j-slides-YYYYMMDD.zip（学習用スライドのPDF。slides/*.md から scripts/slides.py で作る。
        本体に入れると10MBを超えるので別にしている。--no-slides で作らない）

zip に入るもの:
- html/  各章をブラウザで読めるHTMLにしたもの（pandoc。--no-html で省く）。
         index.html の目次は本編とAI関連（html/ai/）の2部に分かれる
- ja/    本編の訳文の Markdown（ja/parts は入れない）
- ai/ja/ AI関連（別冊）の訳文の Markdown
- images/ 図
- glossary.md、README.md、NOTICE.txt（利用条件の注意）
- en/・ai/en/ 英語原文（--with-en を付けたときだけ）

本編は ../images/、別冊は ../../images/ を参照する（HTML版も同じ深さに置く）ので、
zip を展開したフォルダの構成のまま開けば図が表示される。
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
- AI関連（別冊、ai/）は serviceinnovation.org のページとブログ記事で、クリエイティブ・コモンズの
  表示がありません（通常の著作権）。翻訳したものを他の人に配布・共有できません。
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
    text = text.replace(f"# {title}\n", "", 1)  # 見出しは pandoc のタイトル欄に出るので本文からは外す
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
    ap.add_argument("--no-slides", action="store_true", help="スライドのPDFを入れない")
    args = ap.parse_args()

    chapters = sorted(Path("ja").glob("[0-9][0-9]-*.md"))
    if len(chapters) != 11:
        sys.exit(f"ja/ の章が11ではない（{len(chapters)}）。先に assemble.py を実行する")
    ai_chapters = sorted(Path("ai/ja").glob("[0-9][0-9]-*.md"))

    decks = sorted(Path("slides").glob("*.md"))
    if decks and not args.no_slides:  # 原稿から作り直してから入れる（古いPDFを入れないため）
        subprocess.run([sys.executable, "-I", "scripts/slides.py", *map(str, decks)], check=True)

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
        for md in ai_chapters:
            add(md, f"ai/ja/{md.name}")
        for img in sorted(Path("images").iterdir()):
            add(img, f"images/{img.name}")
        if args.with_en:
            for md in sorted(Path("en").glob("*.md")):
                add(md, f"en/{md.name}")
            for md in sorted(Path("ai/en").glob("*.md")):
                add(md, f"ai/en/{md.name}")
        if not args.no_html:
            with tempfile.TemporaryDirectory() as tmp:
                index = ["# KCS ドキュメント 日本語訳", "", "NOTICE.txt の利用条件も読んでください。", "",
                         "## 本編（KCS ライブラリ）", ""]
                Path(tmp, "ai").mkdir()
                for book, mds, sub in (("main", chapters, ""), ("ai", ai_chapters, "ai/")):
                    if book == "ai" and mds:
                        index += ["", "## AI関連（別冊）", ""]
                    for md in mds:
                        out = Path(tmp) / sub / f"{md.stem}.html"
                        to_html(md, out)
                        add(out, f"html/{sub}{out.name}")
                        title = md.read_text(encoding="utf-8").splitlines()[0][2:]
                        index.append(f"- [{title}]({sub}{md.stem}.html)")
                idx_md = Path(tmp) / "index.md"
                idx_md.write_text("\n".join(index) + "\n", encoding="utf-8")
                to_html(idx_md, Path(tmp) / "index.html")
                add(Path(tmp) / "index.html", "html/index.html")

    outputs = [zpath]
    if decks and not args.no_slides:
        spath = Path("dist") / f"kcs-j-slides-{datetime.date.today():%Y%m%d}.zip"
        with zipfile.ZipFile(spath, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{spath.stem}/NOTICE.txt", NOTICE)
            for md in decks:
                z.write(Path("dist/slides") / f"{md.stem}.pdf", f"{spath.stem}/{md.stem}.pdf")
        outputs.append(spath)

    for path in outputs:
        size = path.stat().st_size / 1024 / 1024
        print(f"{path}（{size:.1f} MB）")
        if size > 10:
            print("注意: 10MB を超えている。メールの添付上限に引っかかるかもしれない", file=sys.stderr)


if __name__ == "__main__":
    main()
