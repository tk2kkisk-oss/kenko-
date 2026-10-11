#!/usr/bin/env python3
"""スキル一覧（docs/index.html と SKILLS.md）を作り直すスクリプト。

使い方:
  python3 scripts/build_catalog.py           # 一覧を作り直す
  python3 scripts/build_catalog.py --sync    # 新しく見つかったスキルの下書きを catalog/skills/ に作ってから作り直す
  python3 scripts/build_catalog.py --check   # 生成物が最新かだけ確認（CI用）

スキルの情報源:
  1. catalog/skills/*.md       … 日本語の解説（人が書く・Claudeが書く）
  2. .claude/skills/*/SKILL.md … このリポジトリに置いたスキル（自動で拾う）
  3. ~/.claude/skills/**/SKILL.md … 手元のClaude Codeに入っているスキル（自動で拾う）
外部ライブラリは使わず、Python標準ライブラリだけで動きます。
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = ROOT / "catalog" / "skills"
TEMPLATE = ROOT / "scripts" / "template.html"
OUT_HTML = ROOT / "docs" / "index.html"
OUT_MD = ROOT / "SKILLS.md"
SCAN_DIRS = [
    (ROOT / ".claude" / "skills", "このリポジトリ"),
    (Path.home() / ".claude" / "skills", "未分類"),
]

CATEGORY_ORDER = [
    "病院・看護の業務", "書類・資料づくり", "デザイン・見た目", "調べもの・学び",
    "Google・ブラウザ・PC操作", "毎日の習慣・自動化", "スキル・設定", "プログラム開発", "未分類",
]
SOURCE_ORDER = ["自作スキル", "このリポジトリ", "Anthropic公式", "Claude Code組み込み", "未分類"]
LIST_FIELDS = {"use_when", "examples", "not_for", "aliases"}


def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def parse_frontmatter(text):
    """--- で囲まれた先頭部分を読む（key: value / - リスト / | ブロック のみ対応）。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta, key = {}, None
    block = None  # ブロック文字列（|）を読んでいる途中のキー
    for line in m.group(1).splitlines():
        if block is not None:
            if line.startswith((" ", "\t")) or not line.strip():
                meta[block] += line.strip() + "\n"
                continue
            meta[block] = meta[block].strip()
            block = None
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(unquote(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2)
            if val in ("|", ">", "|-", ">-"):
                block = key
                meta[key] = ""
            else:
                meta[key] = unquote(val) if val else []
    if block is not None:
        meta[block] = meta[block].strip()
    return meta, m.group(2).strip()


def as_list(v):
    if isinstance(v, list):
        return v
    return [v] if v else []


def load_catalog():
    entries = {}
    for path in sorted(CATALOG_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        sid = meta.get("id") or path.stem
        tags = meta.get("tags", "")
        entries[sid] = {
            "id": sid,
            "name": meta.get("name") or sid,
            "command": meta.get("command") if isinstance(meta.get("command"), str) else "",
            "category": meta.get("category") or "未分類",
            "source": meta.get("source") or "未分類",
            "summary": meta.get("summary") or "",
            "tags": [t.strip() for t in tags.split(",") if t.strip()] if isinstance(tags, str) else tags,
            "use_when": as_list(meta.get("use_when")),
            "examples": as_list(meta.get("examples")),
            "not_for": as_list(meta.get("not_for")),
            "aliases": as_list(meta.get("aliases")),
            "note": body,
            "needs_review": str(meta.get("needs_review", "")).lower() == "true",
            "file": str(path.relative_to(ROOT)),
        }
    return entries


def discover_installed():
    """SKILL.md を探して {id: (name, description, 由来)} を返す。"""
    found = {}
    for base, origin in SCAN_DIRS:
        if not base.is_dir():
            continue
        for skill_md in sorted(base.rglob("SKILL.md")):
            rel = skill_md.relative_to(base)
            if any(p.startswith(".") for p in rel.parts) or len(rel.parts) > 4:
                continue
            meta, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
            dir_id = skill_md.parent.name
            name = meta.get("name") if isinstance(meta.get("name"), str) else ""
            desc = meta.get("description") if isinstance(meta.get("description"), str) else ""
            found.setdefault(dir_id, {"name": name or dir_id, "description": desc, "origin": origin})
    return found


def find_new(entries, installed):
    known = set(entries)
    for e in entries.values():
        known.update(e["aliases"])
    return {sid: info for sid, info in installed.items()
            if sid not in known and info["name"] not in known}


def write_stub(sid, info):
    """日本語解説の下書き（英語の説明のまま）を作る。"""
    desc = " ".join(info["description"].split()) or "（説明なし）"
    text = (
        "---\n"
        f"id: {sid}\n"
        f"name: {sid}\n"
        f"command: /{sid}\n"
        "category: 未分類\n"
        f"source: {info['origin']}\n"
        f"summary: {json.dumps(desc, ensure_ascii=False)}\n"
        "tags: \n"
        "use_when:\n"
        "needs_review: true\n"
        "---\n"
    )
    (CATALOG_DIR / f"{sid}.md").write_text(text, encoding="utf-8")


def stub_entry(sid, info):
    return {
        "id": sid, "name": sid, "command": f"/{sid}", "category": "未分類",
        "source": info["origin"], "summary": " ".join(info["description"].split()),
        "tags": [], "use_when": [], "examples": [], "not_for": [], "aliases": [],
        "note": "", "needs_review": True, "file": "",
    }


def sort_key(e):
    def idx(order, v):
        return order.index(v) if v in order else len(order)
    return (idx(CATEGORY_ORDER, e["category"]), idx(SOURCE_ORDER, e["source"]), e["id"])


def render_markdown(skills, generated):
    lines = [
        "# Claude Code スキル一覧",
        "",
        f"全 {len(skills)} 件 ／ 最終更新 {generated}",
        "",
        "検索できる一覧ページは `docs/index.html` です（GitHub Pages で公開できます）。",
        "このファイルは `scripts/build_catalog.py` が自動で作っています。直接編集せず、`catalog/skills/` を編集してください。",
        "",
    ]
    current = None
    for s in skills:
        if s["category"] != current:
            current = s["category"]
            lines += [f"## {current}", ""]
        cmd = f" `{s['command']}`" if s["command"] else ""
        flag = " ⚠️解説準備中" if s["needs_review"] else ""
        lines.append(f"### {s['name']}{cmd}{flag}")
        lines.append("")
        lines.append(f"{s['summary']}  ")
        lines.append(f"<sub>{s['source']} ・ id: `{s['id']}`</sub>")
        lines.append("")
        if s["use_when"]:
            lines.append("**こんな時に**")
            lines += [f"- {u}" for u in s["use_when"]]
            lines.append("")
        if s["examples"]:
            lines.append("**頼み方の例**")
            lines += [f"- {x}" for x in s["examples"]]
            lines.append("")
        if s["not_for"]:
            lines.append("**向いていない時**")
            lines += [f"- {x}" for x in s["not_for"]]
            lines.append("")
        if s["note"]:
            lines += [s["note"], ""]
    return "\n".join(lines).rstrip() + "\n"


def render_fragment(skills, generated):
    data = json.dumps(skills, ensure_ascii=False).replace("</", "<\\/")
    tpl = TEMPLATE.read_text(encoding="utf-8")
    return tpl.replace("/*__SKILLS_DATA__*/[]", data).replace("__GENERATED_AT__", generated)


def render_html(fragment):
    return (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
    )


def main():
    ap = argparse.ArgumentParser(description="スキル一覧を作り直す")
    ap.add_argument("--sync", action="store_true", help="新しいスキルの下書きを catalog/skills/ に作る")
    ap.add_argument("--check", action="store_true", help="生成物が最新か確認するだけ（差があれば終了コード1）")
    ap.add_argument("--fragment", metavar="PATH", help="<html>等を含まないページ断片も書き出す")
    ap.add_argument("--quiet", action="store_true", help="新しいスキルがない時は何も表示しない")
    args = ap.parse_args()

    entries = load_catalog()
    new = find_new(entries, discover_installed())
    if new and args.sync:
        for sid, info in new.items():
            write_stub(sid, info)
        entries = load_catalog()
    else:
        for sid, info in new.items():
            entries[sid] = stub_entry(sid, info)

    skills = sorted(entries.values(), key=sort_key)
    generated = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    fragment = render_fragment(skills, generated)
    html, md = render_html(fragment), render_markdown(skills, generated)

    def strip_time(s):
        return re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", "", s)

    old_html = OUT_HTML.read_text(encoding="utf-8") if OUT_HTML.exists() else ""
    old_md = OUT_MD.read_text(encoding="utf-8") if OUT_MD.exists() else ""
    changed = strip_time(old_html) != strip_time(html) or strip_time(old_md) != strip_time(md)

    if args.check:
        if changed:
            print("スキル一覧が古くなっています。python3 scripts/build_catalog.py を実行してください。")
            sys.exit(1)
        print("スキル一覧は最新です。")
        return

    if changed:
        OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
        OUT_HTML.write_text(html, encoding="utf-8")
        OUT_MD.write_text(md, encoding="utf-8")
    if args.fragment:
        Path(args.fragment).write_text(fragment, encoding="utf-8")

    pending = [s["id"] for s in skills if s["needs_review"]]
    if new:
        verb = "下書きを作りました" if args.sync else "見つかりました（--sync で下書きを作れます）"
        print(f"[スキル一覧] 新しいスキルが{len(new)}件{verb}: {', '.join(sorted(new))}")
    if pending and (new or not args.quiet):
        print(f"[スキル一覧] 日本語の解説がまだのスキル: {', '.join(pending)}"
              " → /update-skill-catalog スキルで解説を書いてください。")
    if not args.quiet:
        state = "更新しました" if changed else "変更はありません"
        print(f"[スキル一覧] 全{len(skills)}件。{state}。")


if __name__ == "__main__":
    main()
