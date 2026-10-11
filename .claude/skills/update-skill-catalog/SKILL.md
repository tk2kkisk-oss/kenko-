---
name: update-skill-catalog
description: このリポジトリのスキル一覧（docs/index.html・SKILLS.md）に新しいスキルを日本語の解説つきで登録し、一覧を作り直す。「スキル一覧を更新して」「新しいスキルを一覧に追加して」と頼まれた時、新しいスキルを作った・入れた直後、またはSessionStartで「日本語の解説がまだのスキル」が報告された時に使う。
---

# スキル一覧の更新

一覧の元データは `catalog/skills/<id>.md`（1スキル1ファイル）。`docs/index.html` と `SKILLS.md` は生成物なので直接編集しない。

## 手順

1. `python3 scripts/build_catalog.py --sync` を実行する。
   - `~/.claude/skills/` と `.claude/skills/` にあって一覧にないスキルの下書きが `catalog/skills/<id>.md` に作られる（`needs_review: true`、説明は英語のまま）。
   - ユーザーが会話で新しいスキルの名前と内容を伝えてきた場合は、下書きがなくても同じ形式でファイルを作る。
2. `needs_review: true` のファイルごとに、元の SKILL.md（`~/.claude/skills/` 以下や `.claude/skills/` 以下を探す）を読み、下の書式で日本語の解説に書き換える。書き終えたら `needs_review` の行を消す。
3. もう一度 `python3 scripts/build_catalog.py` を実行し、エラーがないこと・件数が増えたことを確認する。
4. 変更をコミットして push する（push すると GitHub Actions が一覧ページを作り直して公開する）。

## 書式

```
---
id: スキルのフォルダ名（SKILL.md の name と違う時は aliases に name を書く）
name: 日本語の短い名前（〜する、〜を作る など動作がわかる形）
command: /呼び出し名（Claudeが自動で使うだけのスキルは空にする）
category: 下のカテゴリから1つ
source: 自作スキル | このリポジトリ | Anthropic公式 | Claude Code組み込み
summary: 1〜2文。何ができるかを専門用語なしで。
tags: 検索に使われそうな言葉をカンマ区切り（同義語・略語も。例: パワポ, PowerPoint, スライド）
use_when:
  - どういう時に向いているか（2〜3個、利用者の場面で書く）
examples:
  - 「実際の頼み方の例」
not_for:
  - 向いていない時（あれば。代わりのスキルも書く）
---
補足（任意。注意点や前提条件を1〜3文で）
```

カテゴリ: 病院・看護の業務 / 書類・資料づくり / デザイン・見た目 / 調べもの・学び / Google・ブラウザ・PC操作 / 毎日の習慣・自動化 / スキル・設定 / プログラム開発

## 書き方のコツ

- 読む人は看護管理者（師長）。IT用語は言い換えるか、かっこで補う。
- `use_when` と `examples` は病棟・院内の具体的な場面にすると探しやすい。
- 自分で作ったスキル（髙塚さん用・病院の業務用）は `source: 自作スキル`。
- 個人名・患者情報などは書かない。
