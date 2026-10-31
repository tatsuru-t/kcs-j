"""ページ単位のMarkdown（work/pages）を、章ごとの大きなファイルにまとめる。

使い方: python3 -I scripts/build.py [作業ディレクトリ]   （既定: work）
出力: en/NN-slug.md と en/README.md

- GROUPS の1要素が1ファイル。intro のページは H1 の直下に見出し無しで置き、
  pages に挙げたページは子孫ごと深さ順に H2, H3 ... として連結する
- ページ本文の見出しは、そのページの見出しより1段下がるようにずらす
- サイト内リンクは、まとめた後のファイルとページのアンカー（#page-ID）へ書き換える
- 各ページ末尾のCCライセンス表示は外し、ファイル冒頭に出典として1回だけ書く
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

SITE = "https://library.serviceinnovation.org"

LICENSES = {
    "by-nc": "[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)",
    "by-nc-nd": "[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)",
}

# (ファイル名, H1, ライセンス, intro のページID, 子孫ごと入れるページID)
GROUPS = [
    ("01-principles-and-core-concepts", "KCS Principles and Core Concepts",
     "by-nc-nd", "352", ["354", "355"]),
    ("02-practices-guide-introduction", "Knowledge-Centered Success: Practices Guide (2027)",
     "by-nc", "7165", ["7098", "7099"]),
    ("03-solve-loop", "The Solve Loop",
     "by-nc", "7117", ["7111", "7115", "7104", "7107"]),
    ("04-evolve-loop-content-health", "The Evolve Loop / Practice 5: Content Health",
     "by-nc", "7151", ["7130"]),
    ("05-process-integration", "Practice 6: Process Integration",
     "by-nc", "7136", None),
    ("06-performance-insight", "Practice 7: Performance Insight",
     "by-nc", "7140", None),
    ("07-change-management", "Practice 8: Change Management",
     "by-nc", "7150", None),
    ("08-lessons-learned-and-purpose", "Lessons Learned and the Purpose Behind the Practices",
     "by-nc", None, ["7153", "8246"]),
    ("09-coach-reference-guide", "KCS Coach Reference Guide",
     "by-nc-nd", "6088", None),
    ("10-measuring-self-service-success", "Measuring Self-Service Success (2027)",
     "by-nc", "3965", None),
    ("11-supplemental-resources", "Supplemental KCS Resources",
     "by-nc-nd", "332", None),
]

LICENSE_LINE = re.compile(
    r"^.*(creativecommons\.org|is licensed under a \[Creative Commons).*$\n?", re.M)
HEADING = re.compile(r"^(#{1,6}) ", re.M)
LINK = re.compile(r"\]\((https?://library\.serviceinnovation\.org/[^)\s]*)\)")


def norm(url_or_path: str) -> str:
    """URLとページパスを比較できる形にそろえる。"""
    p = url_or_path.split("#")[0].split("?")[0]
    p = p.removeprefix(SITE).strip("/")
    return urllib.parse.unquote(p).replace(" ", "_").lower()


def subtree(pages, root_id):
    """manifest は深さ優先の並びなので、root から次の同じ深さまでが子孫。"""
    idx = next(i for i, p in enumerate(pages) if p["id"] == root_id)
    depth = pages[idx]["depth"]
    out = [pages[idx]]
    for p in pages[idx + 1:]:
        if p["depth"] <= depth:
            break
        out.append(p)
    return out


def shift_headings(md: str, base: int) -> str:
    """本文の見出しを base 段目から始まるようにずらす（6段を超えたら太字にする）。"""
    levels = [len(m.group(1)) for m in HEADING.finditer(md)]
    if not levels:
        return md
    delta = base - min(levels)

    def repl(m):
        lv = len(m.group(1)) + delta
        return "#" * lv + " " if lv <= 6 else "**▸** "
    return HEADING.sub(repl, md)


def plan(pages):
    """各ファイルに入るページと見出しの深さを決める。"""
    by_id = {p["id"]: p for p in pages}
    files = []
    for name, title, lic, intro, roots in GROUPS:
        entries = []
        if intro:
            entries.append((by_id[intro], 1))  # H1 直下
        if roots is None:  # intro の子孫を全部
            members = subtree(pages, intro)[1:]
        else:
            members = [p for r in roots for p in subtree(pages, r)]
        if members:
            d0 = min(p["depth"] for p in members)
            entries += [(p, 2 + p["depth"] - d0) for p in members]
        files.append((name, title, lic, entries))
    return files


def main():
    work = Path(sys.argv[1] if len(sys.argv) > 1 else "work")
    pages = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    files = plan(pages)

    placed = [p["id"] for _, _, _, es in files for p, _ in es]
    missing = [p["title"] for p in pages if p["id"] not in placed]
    if missing or len(placed) != len(set(placed)):
        sys.exit(f"ページの割り当てに漏れか重複がある: {missing}")

    # ページパス → まとめた後のリンク先
    target = {}
    for name, _, _, entries in files:
        for p, level in entries:
            anchor = "" if level == 1 else f"#page-{p['id']}"
            target[norm(p["path"])] = f"{name}.md{anchor}"

    def relink(md: str) -> str:
        def repl(m):
            t = target.get(norm(m.group(1)))
            return f"]({t})" if t else m.group(0)
        return LINK.sub(repl, md)

    outdir = Path("en")
    outdir.mkdir(exist_ok=True)
    index = ["# KCS ドキュメント（英語原文・章ごとにまとめ直したもの）", ""]
    for name, title, lic, entries in files:
        parts = [f"# {title}", ""]
        parts.append("> 出典: Consortium for Service Innovation, "
                     f"*{title}* — {LICENSES[lic]}  ")
        parts.append("> 元のページ:")
        for p, _ in entries:
            parts.append(f"> - [{p['title']}]({p['url']})")
        parts.append("")
        for p, level in entries:
            body = (work / "pages" / f"{p['id']}.md").read_text(encoding="utf-8")
            body = LICENSE_LINE.sub("", body).strip()
            body = relink(body)
            if level == 1:
                parts += [shift_headings(body, 2), ""]
            else:
                parts += [f'<a id="page-{p["id"]}"></a>', "",
                          f"{'#' * level} {p['title']}", ""]
                parts += [shift_headings(body, level + 1), ""]
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip() + "\n"
        (outdir / f"{name}.md").write_text(text, encoding="utf-8")
        index.append(f"- [{title}]({name}.md)（{len(entries)}ページ / {len(text):,}字）")
        print(f"{name}: {len(entries)}ページ {len(text):,}字")
    (outdir / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
