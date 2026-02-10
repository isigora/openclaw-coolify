#!/usr/bin/env python3
"""Word Tree 웹 서버.

기능:
- 정적 웹(트리맵 UI) 제공
- 로컬 taxonomy 검색
- CEDICT SQLite 검색
- 위키(위키백과/위키낱말사전) 요약 조회

실행:
  python tools/word_tree/server.py --port 8787
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TREE = ROOT / "data/lexicon/word_taxonomy_zh.json"
DEFAULT_DB = ROOT / "data/lexicon/cedict.db"
WEB_ROOT = ROOT / "web/word-tree"


def load_tree(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def walk_tree(tree: dict, target: str):
    def dfs(name, node, path):
        aliases = node.get("aliases", [])
        if name == target or target in aliases:
            return {
                "path": path + [name],
                "node": node,
                "matched_by": "alias" if (target in aliases and name != target) else "name",
            }
        for child_name, child_node in node.get("children", {}).items():
            got = dfs(child_name, child_node, path + [name])
            if got:
                return got
        return None

    for root_name, root_node in tree.items():
        got = dfs(root_name, root_node, [])
        if got:
            return got
    return None


def surrounding_context(tree: dict, path: list[str]) -> dict:
    node = tree
    current = None
    lineage: list[dict] = []
    for i, step in enumerate(path):
        if i == 0:
            current = node[step]
            lineage.append({"name": step, "label": current.get("label", "")})
        else:
            current = current.get("children", {}).get(step)
            if current is None:
                break
            lineage.append({"name": step, "label": current.get("label", "")})

    parent_name = path[-2] if len(path) > 1 else None
    siblings = []
    if len(path) >= 2:
        parent = tree[path[0]]
        for p in path[1:-1]:
            parent = parent.get("children", {}).get(p, {})
        siblings = [k for k in parent.get("children", {}).keys() if k != path[-1]]

    children = list(current.get("children", {}).keys()) if current else []
    return {
        "lineage": lineage,
        "parent": parent_name,
        "siblings": siblings,
        "children": children,
    }


def lookup_cedict(db_path: Path, word: str) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT traditional, simplified, pinyin, definitions
            FROM entries
            WHERE simplified = ? OR traditional = ?
            LIMIT 20
            """,
            (word, word),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def fetch_mediawiki_extract(project: str, word: str) -> str | None:
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "titles": word,
        }
    )
    url = f"https://{project}.org/w/api.php?{params}"
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        pages = payload.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = (page.get("extract") or "").strip()
            if extract:
                return extract
    except Exception:
        return None
    return None


class Handler(SimpleHTTPRequestHandler):
    tree = load_tree(DEFAULT_TREE)
    db_path = DEFAULT_DB

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/tree":
            self.send_json(Handler.tree)
            return

        if parsed.path == "/api/lookup":
            q = urllib.parse.parse_qs(parsed.query)
            word = (q.get("word") or [""])[0].strip()
            if not word:
                self.send_json({"error": "word is required"}, code=400)
                return

            local_match = walk_tree(Handler.tree, word)
            local_context = (
                surrounding_context(Handler.tree, local_match["path"]) if local_match else None
            )
            cedict = lookup_cedict(Handler.db_path, word)
            wiki = fetch_mediawiki_extract("zh.wikipedia", word)
            wiktionary = fetch_mediawiki_extract("zh.wiktionary", word)

            self.send_json(
                {
                    "word": word,
                    "local_match": local_match,
                    "local_context": local_context,
                    "cedict": cedict,
                    "wikipedia": wiki,
                    "wiktionary": wiktionary,
                }
            )
            return

        return super().do_GET()

    def translate_path(self, path: str) -> str:
        parsed = urllib.parse.urlparse(path)
        clean = parsed.path.lstrip("/") or "index.html"
        return str((WEB_ROOT / clean).resolve())

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Word Tree 웹 서버 실행")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--tree", default=str(DEFAULT_TREE), help="taxonomy JSON 경로")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="CEDICT SQLite 경로")
    args = parser.parse_args()

    Handler.tree = load_tree(Path(args.tree))
    Handler.db_path = Path(args.db)

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"Word Tree server listening on http://0.0.0.0:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
