"""KCSライブラリ（MindTouch）からページツリーと本文HTMLを取得する。

使い方: python3 -I scripts/fetch.py [出力先ディレクトリ]   （既定: work）

- ツリーは /@api/deki/pages/=KCS/tree で一度に取る
- 本文は /@api/deki/pages/{id}/contents?format=html で1ページずつ取る
- 取得済みのページは飛ばすので、途中で止まっても再実行すれば続きから取れる
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://library.serviceinnovation.org/@api/deki"
UA = "kcs-j-fetch/1.0 (personal translation)"
INTERVAL_SEC = 1.0

# 対象にする新しい版のガイド（KCS/ 直下のパス）。順序は出力の順序になる
SCOPE = [
    "KCS/Principles_and_Core_Concepts",
    "KCS/Knowledge-Centered_Success_Practices_Guide",
    "KCS/Coach_Reference_Guide",
    "KCS/Measuring_Self-Service_Success",
    "KCS/KCS_Resources",
]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                return res.read()
        except Exception as e:  # ネットワーク断・5xx は少し待って再試行
            if attempt == 3:
                raise
            print(f"  再試行 {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def walk(node: ET.Element, depth: int, out: list, parent_id):
    """ツリーを深さ優先・サイト上の並び順でたどり、平らな一覧にする。"""
    pid = node.get("id")
    out.append({
        "id": pid,
        "title": node.findtext("title"),
        "path": node.findtext("path"),
        "url": node.findtext("uri.ui"),
        "depth": depth,
        "parent": parent_id,
    })
    for child in node.findall("./subpages/page"):
        walk(child, depth + 1, out, pid)


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "work")
    rawdir = outdir / "raw"
    rawdir.mkdir(parents=True, exist_ok=True)

    tree = ET.fromstring(get(f"{BASE}/pages/=KCS/tree?format=xml"))
    by_path = {p.findtext("path"): p for p in tree.iter("page")}

    pages = []
    for root_path in SCOPE:
        node = by_path.get(root_path)
        if node is None:
            sys.exit(f"ツリーに見つからない: {root_path}")
        walk(node, 0, pages, None)

    (outdir / "manifest.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(pages)} ページ")

    for i, p in enumerate(pages, 1):
        dest = rawdir / f"{p['id']}.xml"
        if dest.exists():
            continue
        print(f"[{i}/{len(pages)}] {p['title']}")
        dest.write_bytes(get(f"{BASE}/pages/{p['id']}/contents?format=html"))
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
