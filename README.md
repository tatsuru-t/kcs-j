# kcs-j

Consortium for Service Innovation の [KCS ライブラリ](https://library.serviceinnovation.org/KCS)
を、読みやすい大きさの章ごとのMarkdownにまとめ直し、日本語に訳したもの。

**個人の学習用。このリポジトリは非公開にしておくこと。** 一部の文書は
CC BY-NC-ND 4.0（改変禁止）で、翻訳・再構成したものは共有できない（下の表）。

## 目次

| # | 章 | 日本語 | 英語原文 | ライセンス |
| --- | --- | --- | --- | --- |
| 01 | 原則とコアコンセプト | [ja](ja/01-principles-and-core-concepts.md) | [en](en/01-principles-and-core-concepts.md) | CC BY-NC-ND 4.0 |
| 02 | プラクティスガイド（2027年版）序文・KCSが機能する理由・KCS記事 | [ja](ja/02-practices-guide-introduction.md) | [en](en/02-practices-guide-introduction.md) | CC BY-NC 4.0 |
| 03 | Solve Loop（プラクティス1〜4） | [ja](ja/03-solve-loop.md) | [en](en/03-solve-loop.md) | CC BY-NC 4.0 |
| 04 | Evolve Loop／プラクティス5：コンテンツの健全性 | [ja](ja/04-evolve-loop-content-health.md) | [en](en/04-evolve-loop-content-health.md) | CC BY-NC 4.0 |
| 05 | プラクティス6：プロセスの統合 | [ja](ja/05-process-integration.md) | [en](en/05-process-integration.md) | CC BY-NC 4.0 |
| 06 | プラクティス7：パフォーマンスの把握 | [ja](ja/06-performance-insight.md) | [en](en/06-performance-insight.md) | CC BY-NC 4.0 |
| 07 | プラクティス8：チェンジマネジメント | [ja](ja/07-change-management.md) | [en](en/07-change-management.md) | CC BY-NC 4.0 |
| 08 | 教訓と避けるべき落とし穴・プラクティスの目的 | [ja](ja/08-lessons-learned-and-purpose.md) | [en](en/08-lessons-learned-and-purpose.md) | CC BY-NC 4.0 |
| 09 | コーチ・リファレンスガイド | [ja](ja/09-coach-reference-guide.md) | [en](en/09-coach-reference-guide.md) | 表示なし（BY-NC-ND とみなす） |
| 10 | セルフサービスの成功の測定（2027年版） | [ja](ja/10-measuring-self-service-success.md) | [en](en/10-measuring-self-service-success.md) | CC BY-NC 4.0 |
| 11 | 補足資料（用語集・参考文献・帰属表示など） | 未訳 | [en](en/11-supplemental-resources.md) | CC BY-NC-ND 4.0（一部ページ） |

新しい版のガイドだけを扱う（KCS v6 と他言語版は対象外）。訳語と表記の決まりは [glossary.md](glossary.md)。

## 作り方

```bash
python3 -I scripts/fetch.py work     # ツリーと本文HTMLを取得（work/raw, work/manifest.json）
python3 -I scripts/convert.py work   # ページ単位のMarkdownへ（work/pages）
python3 -I scripts/build.py work     # 章ごとに11ファイルへまとめる（en/）
python3 -I scripts/assemble.py 01    # 分割して訳した ja/parts/01*.md を1ファイルに（ja/）
```

必要なもの: Python 3、`beautifulsoup4`、`pandoc`。`work/` は作り直せるので git に入れていない。

- 本文は MindTouch の API（`/@api/deki/pages/{id}/contents`）から取る。HTMLの画面は解析しない
- ファイルの区切りは `scripts/build.py` の `GROUPS` で決めている（1ファイル1.6万〜8万字）
- サイト内リンクは、まとめた後のファイルとページのアンカー（`#page-ID`）に書き換える。
  対象外のページ（v6・会員向けwiki・アーカイブ）へのリンクは元のURLのまま
- 訳文は `ja/parts/` に分けて書き、`assemble.py` でまとめる。まとめるときに、ページの
  アンカーと見出しの数が英語版と一致するかを検査する
