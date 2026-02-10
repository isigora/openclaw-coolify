#!/usr/bin/env python3
"""词语来龙去脉追踪器。

使用示例：
  python tools/word_tree/trace_word.py 妈妈
  python tools/word_tree/trace_word.py 看 --data data/lexicon/word_taxonomy_zh.json
"""

from __future__ import annotations

import argparse
import json
from difflib import get_close_matches
from pathlib import Path
from typing import Any


def load_taxonomy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def walk_tree(tree: dict[str, Any], target: str) -> dict[str, Any] | None:
    """在树中查找目标词，返回路径与节点详情。"""

    def dfs(name: str, node: dict[str, Any], path: list[str]) -> dict[str, Any] | None:
        aliases = node.get("aliases", [])
        if name == target or target in aliases:
            return {"path": path + [name], "node": node, "matched_by": "alias" if target in aliases and name != target else "name"}

        for child_name, child_node in node.get("children", {}).items():
            found = dfs(child_name, child_node, path + [name])
            if found:
                return found
        return None

    for root_name, root_node in tree.items():
        found = dfs(root_name, root_node, [])
        if found:
            return found
    return None


def collect_terms(tree: dict[str, Any]) -> list[str]:
    terms: list[str] = []

    def dfs(name: str, node: dict[str, Any]) -> None:
        terms.append(name)
        terms.extend(node.get("aliases", []))
        for child_name, child_node in node.get("children", {}).items():
            dfs(child_name, child_node)

    for root_name, root_node in tree.items():
        dfs(root_name, root_node)
    return terms


def format_result(word: str, result: dict[str, Any]) -> str:
    node = result["node"]
    path = result["path"]
    matched_by = result["matched_by"]

    lines = [
        "⚡ 词语来龙去脉",
        f"- 查询词: {word}",
        f"- 匹配方式: {'别名' if matched_by == 'alias' else '词条名'}",
        f"- 全局路径: {' > '.join(path)}",
        f"- 词性: {node.get('pos', '未标注')}",
        f"- 概念说明: {node.get('label', '无')}",
    ]

    aliases = node.get("aliases", [])
    if aliases:
        lines.append(f"- 近义/别名: {'、'.join(aliases)}")

    related = node.get("related", [])
    if related:
        lines.append(f"- 相关词: {'、'.join(related)}")

    examples = node.get("examples", [])
    if examples:
        lines.append("- 例句:")
        for sentence in examples:
            lines.append(f"  • {sentence}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="输入一个词，展示它在知识树中的上下文位置")
    parser.add_argument("word", help="要查询的词")
    parser.add_argument(
        "--data",
        default="data/lexicon/word_taxonomy_zh.json",
        help="词语知识树 JSON 文件路径",
    )
    args = parser.parse_args()

    taxonomy = load_taxonomy(Path(args.data))
    result = walk_tree(taxonomy, args.word)
    if result:
        print(format_result(args.word, result))
        return

    candidates = collect_terms(taxonomy)
    guesses = get_close_matches(args.word, candidates, n=5, cutoff=0.3)
    print(f"未找到词语：{args.word}")
    if guesses:
        print(f"你是不是想查：{'、'.join(dict.fromkeys(guesses))}？")


if __name__ == "__main__":
    main()
