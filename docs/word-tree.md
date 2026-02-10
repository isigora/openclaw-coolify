# 词语大树（Word Context Tree）

这个小工具对应你的想法：

> 输入一个词，立刻看到它在整体知识树里的“位置 + 关系 + 例子”。

## 运行

```bash
python tools/word_tree/trace_word.py 妈妈
python tools/word_tree/trace_word.py 看
python tools/word_tree/trace_word.py 母亲
```

## 数据结构

词库文件：`data/lexicon/word_taxonomy_zh.json`

- 每个节点可以包含：
  - `label`：概念说明
  - `children`：子分类
  - `pos`：词性（如名词/动词）
  - `aliases`：别名/近义词
  - `examples`：例句
  - `related`：关联词

## 扩展建议

1. 扩大词库（按“实体 / 行为 / 抽象概念”等分层）。
2. 接入数据库（SQLite/Neo4j）以支持更大规模检索。
3. 增加 Web UI，把树状路径做成可点击导航。
4. 增加“跨语言映射”，如中文词 -> 英文词 -> 词源。
