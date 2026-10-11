# Claude スキル帳

Claude Code で使えるスキルを、日本語で「どんな時に使うか」から探せる一覧です。

- **検索できる一覧ページ**: [`docs/index.html`](docs/index.html)（GitHub Pages で公開すると、スマホからも見られます）
- **文字だけの一覧**: [`SKILLS.md`](SKILLS.md)（GitHub 上でそのまま読めます）

## ページでできること

- やりたいこと（「シフト」「Excel」「ポスター」など）で検索。全角・半角、カタカナ・ひらがなの違いは気にしなくて大丈夫です。
- カテゴリ（病院・看護の業務、書類・資料づくり など）や種類（自作スキル、Anthropic公式 など）で絞り込み。
- 各スキルに「こんな時に」「頼み方の例」「向いていない時」を表示。
- `/コマンド名` をクリックするとコピーできます。

## 新しいスキルを追加したら（一覧の自動更新）

| どこで | 何が起きるか |
|---|---|
| このリポジトリで Claude Code を開いた時 | 起動時に `~/.claude/skills/` と `.claude/skills/` を調べ、一覧にないスキルの下書きを `catalog/skills/` に自動で作ります。 |
| Claude に「スキル一覧を更新して」と頼んだ時 | `/update-skill-catalog` スキルが、下書きを日本語の解説に書き直して一覧を作り直します。 |
| GitHub に push した時 | GitHub Actions が一覧（`docs/index.html`・`SKILLS.md`）を作り直してコミットし、GitHub Pages に公開します。 |

手で追加したい時は、`catalog/skills/` に既存のファイルをまねて `<スキル名>.md` を1つ作り、push するだけで一覧に載ります。

## 仕組み

```
catalog/skills/*.md        ← 1スキル1ファイルの日本語解説（ここを編集する）
.claude/skills/*/SKILL.md  ← このリポジトリに置いたスキル（自動で拾う）
scripts/build_catalog.py   ← 一覧を作るスクリプト（Python標準ライブラリのみ）
scripts/template.html      ← 一覧ページのひな形
docs/index.html, SKILLS.md ← 自動生成（直接編集しない）
```

手元で作り直す: `python3 scripts/build_catalog.py`（新しいスキルの下書きも作るなら `--sync`）

## GitHub Pages の公開設定（最初に1回だけ）

1. GitHub のリポジトリで **Settings → Pages** を開く
2. **Source** を **GitHub Actions** にする
3. 既定のブランチ（main など）に push すると `https://<ユーザー名>.github.io/<リポジトリ名>/` で見られるようになります
