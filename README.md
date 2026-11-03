# kcs-j

Consortium for Service Innovation の [KCS ライブラリ](https://library.serviceinnovation.org/KCS)
を、読みやすい大きさの章ごとのMarkdownにまとめ直し、日本語に訳したもの（本編）。
あわせて、serviceinnovation.org のAI関連のページを別冊（`ai/`）として訳している。

**個人の学習用。このリポジトリは非公開にしておくこと。** 一部の文書は
CC BY-NC-ND 4.0（改変禁止）で、翻訳・再構成したものは共有できない（下の表）。

## 目次：本編（KCS ライブラリ）

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
| 11 | 補足資料（用語集・参考文献・帰属表示など） | [ja](ja/11-supplemental-resources.md) | [en](en/11-supplemental-resources.md) | CC BY-NC-ND 4.0（一部ページ） |

KCS ライブラリの新しい版のガイドだけを扱う（KCS v6 と他言語版は対象外）。

## 目次：AI関連（別冊、`ai/`）

serviceinnovation.org の、AIに関するページとブログ記事。`scripts/fetch_web.py` で取り込んだ。
どれもクリエイティブ・コモンズの表示が無い（フッターは © のみ）ので、通常の著作権として扱う。

| # | ページ | 日本語 | 英語原文 |
| --- | --- | --- | --- |
| 01 | AI導入の要点（AI Implementation Essentials） | [ja](ai/ja/01-ai-implementation-essentials.md) | [en](ai/en/01-ai-implementation-essentials.md) |
| 02 | ナレッジを動力とするAI（Knowledge-Powered AI） | [ja](ai/ja/02-knowledge-powered-ai.md) | [en](ai/en/02-knowledge-powered-ai.md) |
| 03 | AIの事例（AI Case Studies：PTC・Akamai・Red Hat） | [ja](ai/ja/03-ai-case-studies.md) | [en](ai/en/03-ai-case-studies.md) |
| 04 | AIプロジェクトが失敗する理由・成功する理由（ブログ、2025-11） | [ja](ai/ja/04-why-ai-projects-fail-or-succeed.md) | [en](ai/en/04-why-ai-projects-fail-or-succeed.md) |
| 05 | エージェント型AIをKCSと Intelligent Swarming に結び付ける（ブログ、2026-02） | [ja](ai/ja/05-connecting-agentic-ai-to-kcs-and-intelligent-swarming.md) | [en](ai/en/05-connecting-agentic-ai-to-kcs-and-intelligent-swarming.md) |

訳語と表記の決まりは本編・別冊共通で [glossary.md](glossary.md)。

## 学習用スライド（`slides/`）

訳文の要点をまとめた個人学習用のスライド。原稿は Markdown（`---` でスライドを区切る）で、
`scripts/slides.py` が pandoc と Chromium（Playwright）だけで16:9のHTMLとPDFを作る（`dist/slides/`）。
PDFは `package.py` が本体とは別の zip（`dist/kcs-j-slides-YYYYMMDD.zip`）にまとめる。

| 原稿 | 内容 |
| --- | --- |
| [slides/01-kcs-overview.md](slides/01-kcs-overview.md) | KCS 本編の要点（29枚）：原則・ダブルループ・8つのプラクティス・役割・測定・落とし穴 |
| [slides/02-ai-and-kcs.md](slides/02-ai-and-kcs.md) | AI × KCS（12枚）：AI導入の要点・事例・失敗の理由・エージェント型AI・本編とのつながり |

## 作り方

```bash
python3 -I scripts/fetch.py work     # ツリーと本文HTMLを取得（work/raw, work/manifest.json）
python3 -I scripts/convert.py work   # ページ単位のMarkdownへ（work/pages）
python3 -I scripts/build.py work     # 章ごとに11ファイルへまとめる（en/）
python3 -I scripts/images.py en ja/parts   # 図を images/ に取り込み、参照を相対パスに（何度実行しても同じ）
python3 -I scripts/assemble.py 01    # 分割して訳した ja/parts/01*.md を1ファイルに（ja/）。図の説明もここで入る
python3 -I scripts/fetch_web.py URL 01-slug "見出し" ai    # 別冊：serviceinnovation.org のページを ai/en/ に
python3 -I scripts/assemble.py 01 ai # 別冊：ai/ja/parts/01*.md を ai/ja/ に
python3 -I scripts/slides.py slides/01-kcs-overview.md    # スライドのHTMLとPDFを dist/slides/ に（はみ出しも検査する）
python3 -I scripts/package.py --publish   # 本編・別冊の訳文・図・HTML版の zip と、スライドのPDFの zip を作り、packages/ に置く
```

必要なもの: Python 3、`beautifulsoup4`、`pandoc`。`work/` は作り直せるので git に入れていない。

- 本文は MindTouch の API（`/@api/deki/pages/{id}/contents`）から取る。HTMLの画面は解析しない
- ファイルの区切りは `scripts/build.py` の `GROUPS` で決めている（1ファイル1.6万〜8万字）
- サイト内リンクは、まとめた後のファイルとページのアンカー（`#page-ID`）に書き換える。
  対象外のページ（v6・会員向けwiki・アーカイブ）へのリンクは元のURLのまま
- 図は `images/` に取り込んである（実体は `files.mtstatic.com` への転送の先にある）。図の中の英語は
  そのままにし、各図の直後に `ja/figures.json` の日本語の説明（ラベルの訳と要点）を差し込む
- `package.py` の zip には HTML版（`html/index.html` から開く）と利用条件の注意（`NOTICE.txt`）が入る。
  最新の zip は [`packages/`](packages/) に置いてある（`--publish` で置き換わり、古い zip は消える）
- 訳文は `ja/parts/` に分けて書き、`assemble.py` でまとめる。まとめるときに、ページの
  アンカーと見出しの数が英語版と一致するかを検査する
