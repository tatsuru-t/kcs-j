# kcs-j

Consortium for Service Innovation の [KCS ライブラリ](https://library.serviceinnovation.org/KCS)
を、読みやすい大きさの章ごとのMarkdownにまとめ直し、日本語に訳すための作業リポジトリ。

## 対象

新しい版のガイドだけを扱う（v6 と他言語版は対象外）。

| ガイド | ページ数 | ライセンス |
| --- | --- | --- |
| KCS Principles and Core Concepts | 17 | CC BY-NC-ND 4.0 |
| Knowledge-Centered Success: Practices Guide (2027) | 44 | CC BY-NC 4.0 |
| KCS Coach Reference Guide | 12 | 表示なし（KCS全体の規定 BY-NC-ND に従う） |
| Measuring Self-Service Success (2027) | 7 | CC BY-NC 4.0 |
| Supplemental KCS Resources | 7 | CC BY-NC-ND 4.0（一部ページ） |

**BY-NC-ND の文書の翻訳・再構成は改変にあたるため、共有できない。**
原文・訳文は `work/` に置き、`.gitignore` でリポジトリから外している。

## 手順

```bash
python3 -I scripts/fetch.py work     # ツリーと本文HTMLを取得（work/raw, work/manifest.json）
python3 -I scripts/convert.py work   # ページ単位のMarkdownへ（work/pages）
python3 -I scripts/build.py work     # 章ごとに11ファイルへまとめる（work/en）
python3 -I scripts/assemble.py 01   # 分割して訳した work/ja/parts/01*.md を1ファイルに（work/ja）
```

必要なもの: Python 3、`beautifulsoup4`、`pandoc`。

- 本文は MindTouch の API（`/@api/deki/pages/{id}/contents`）から取る。HTMLの画面は解析しない
- 訳語と表記の決まりは [glossary.md](glossary.md)
- ファイルの区切りは `scripts/build.py` の `GROUPS` で決めている（1ファイル1.6万〜8万字）
- サイト内リンクは、まとめた後のファイルとページのアンカー（`#page-ID`）に書き換える。
  対象外のページ（v6・会員向けwiki）へのリンクは元のURLのまま
