"""訳文と図を1つの zip にまとめる（メールで送って手元で読むため）。

使い方: python3 -I scripts/package.py [--with-en] [--no-html] [--with-slides] [--aspx] [--publish]
出力:   dist/kcs-j-YYYYMMDD.zip（訳文の Markdown と HTML版・図・学習用スライドをすべて1つに）
        --publish を付けると、HTML版をリポジトリの html/ に作り直し、できた zip を packages/ にコピーし、
        packages/ の古い zip を消す
        （packages/ はリポジトリに入れている。dist/ は入れていない）

zip に入るもの:
- html/  各章をブラウザで読めるHTMLにしたもの（pandoc。--no-html で省く）。
         index.html の目次は scripts/toc.py --html で作る（本編とAI関連（html/ai/）の2部、節まで）。
         --publish のときはリポジトリの html/ にも置く（作り直すたびに前の出力は消す）
- ja/    本編の訳文の Markdown（ja/parts は入れない）
- ai/ja/ AI関連（別冊）の訳文の Markdown
- images/ 図
- glossary.md、README.md（利用条件は README.md に書いてある）
- slides/ 学習用スライドのPDFと原稿の Markdown（PDFは slides/*.md から scripts/slides.py で
          作り直してから入れる。--with-slides を付けたときだけ）
- en/・ai/en/ 英語原文（--with-en を付けたときだけ）

--aspx を付けると、HTML版の拡張子を .aspx にしたものを別の zip（dist/kcs-j-aspx-YYYYMMDD.zip）にも作る。
SharePoint のドキュメントライブラリでは .html はダウンロードされてしまうので、.aspx にしてブラウザで
開かせるため（中身は同じHTMLで、章どうしのリンクだけ .aspx に付け替える）。テナントの設定（カスタム
スクリプトの禁止）によってはアップロードできないか、開いてもダウンロードになる。packages/ には置かない

本編は ../images/、別冊は ../../images/ を参照する（HTML版も同じ深さに置く）ので、
zip を展開したフォルダの構成のまま開けば図が表示される。
"""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

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


def build_html(html_dir: Path, chapters: list, ai_chapters: list) -> None:
    """本編と別冊の各章、節まで入れた目次（index.html）を html_dir に作る。前の出力は消す。"""
    for old in html_dir.rglob("*.html") if html_dir.exists() else []:
        old.unlink()
    (html_dir / "ai").mkdir(parents=True, exist_ok=True)
    for md in chapters:
        to_html(md, html_dir / f"{md.stem}.html")
    for md in ai_chapters:
        to_html(md, html_dir / "ai" / f"{md.stem}.html")
    index = subprocess.run([sys.executable, "-I", "scripts/toc.py", "--html"],
                           capture_output=True, text=True, check=True).stdout.splitlines()
    with tempfile.TemporaryDirectory() as tmp:
        idx_md = Path(tmp) / "index.md"
        idx_md.write_text("\n".join(index) + "\n", encoding="utf-8")
        to_html(idx_md, html_dir / "index.html")


def build_aspx_zip(html_dir: Path, name: str) -> Path:
    """HTML版を .aspx にして、図・README と一緒に zip にする（SharePoint にアップロードする用）。"""
    zpath = Path("dist") / f"{name}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write("README.md", f"{name}/README.md")
        for img in sorted(Path("images").iterdir()):
            z.write(img, f"{name}/images/{img.name}")
        for path in sorted(html_dir.rglob("*.html")):
            text = path.read_text(encoding="utf-8")
            if "<%" in text:  # ASP.NET の記法と誤解されると表示できない
                sys.exit(f"{path} に <% がある。.aspx にできない")
            text = re.sub(r'href="(?!https?:|mailto:)([^"#]*)\.html(#[^"]*)?"', r'href="\1.aspx\2"', text)
            arc = path.relative_to(html_dir).with_suffix(".aspx").as_posix()
            z.writestr(f"{name}/aspx/{arc}", text)
    return zpath


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-en", action="store_true", help="英語原文も入れる")
    ap.add_argument("--no-html", action="store_true", help="HTML版を作らない")
    ap.add_argument("--with-slides", action="store_true", help="学習用スライドも入れる")
    ap.add_argument("--aspx", action="store_true", help="SharePoint 用に .aspx 版の zip も作る")
    ap.add_argument("--publish", action="store_true", help="HTML版を html/ に、zip を packages/ に置き、古い zip を消す")
    args = ap.parse_args()

    chapters = sorted(Path("ja").glob("[0-9][0-9]-*.md"))
    if len(chapters) != 11:
        sys.exit(f"ja/ の章が11ではない（{len(chapters)}）。先に assemble.py を実行する")
    ai_chapters = sorted(Path("ai/ja").glob("[0-9][0-9]-*.md"))

    decks = sorted(Path("slides").glob("*.md"))
    if decks and args.with_slides:  # 原稿から作り直してから入れる（古いPDFを入れないため）
        subprocess.run([sys.executable, "-I", "scripts/slides.py", *map(str, decks)], check=True)

    # HTML版：--publish ならリポジトリの html/ に、そうでなければ一時フォルダに作る。
    # どちらも images/ と同じ階層に置くので、../images/・../../images/ の参照がそのまま通る
    tmp = tempfile.TemporaryDirectory()
    html_dir = Path("html") if args.publish else Path(tmp.name) / "html"
    if not args.no_html:
        build_html(html_dir, chapters, ai_chapters)

    Path("dist").mkdir(exist_ok=True)
    name = f"kcs-j-{datetime.date.today():%Y%m%d}"
    zpath = Path("dist") / f"{name}.zip"

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        def add(path: Path, arc: str):
            z.write(path, f"{name}/{arc}")

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
        if decks and args.with_slides:
            for md in decks:
                add(md, f"slides/{md.name}")
                add(Path("dist/slides") / f"{md.stem}.pdf", f"slides/{md.stem}.pdf")
        if not args.no_html:
            for path in sorted(html_dir.rglob("*.html")):
                add(path, f"html/{path.relative_to(html_dir).as_posix()}")

    outputs = [zpath]
    if args.aspx and not args.no_html:
        outputs.append(build_aspx_zip(html_dir, f"kcs-j-aspx-{datetime.date.today():%Y%m%d}"))

    for path in outputs:
        size = path.stat().st_size / 1024 / 1024
        print(f"{path}（{size:.1f} MB）")
        if size > 10:
            print("注意: 10MB を超えている。メールの添付上限に引っかかるかもしれない", file=sys.stderr)

    if args.publish:
        pub = Path("packages")
        pub.mkdir(exist_ok=True)
        for old in pub.glob("kcs-j-*.zip"):  # 古い zip（以前のスライド専用の zip も含む）を消す
            if old.name != zpath.name:
                old.unlink()
                print(f"削除 {old}")
        for path in outputs:
            shutil.copy2(path, pub / path.name)
            print(f"配置 {pub / path.name}")


if __name__ == "__main__":
    main()
