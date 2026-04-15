---
title: 手写解析器陷阱
type: pitfall
agent: hermes
created: 2026-04-15
updated: 2026-04-15
tags: [pitfall, parser, yaml, json, regex]
---

# 手写解析器陷阱

> **核心教训**：永远不要因为"看起来简单"就手写解析器。标准库的存在是有原因的。

## 典型场景

- 需要解析 YAML frontmatter → 用手写字符串 split
- 需要解析 JSON → 用正则匹配
- 需要解析 CSV → 用 `line.split(',')`
- 需要解析 URL query string → 用手写 `split('&')`

## 为什么这是坑

| 你以为的 | 实际的 |
|---------|--------|
| "就几行 YAML，手写更快" | 你的实现不支持 inline list、多行字符串、转义引号、注释 |
| "正则匹配 JSON 就够了" | JSON 嵌套一层你就傻了 |
| `line.split(',')` 能解析 CSV | 字段里包含逗号或换行时直接崩盘 |
| "这个输入格式很固定" | 明天就会有人传一个边缘 case 进来 |

## 正确做法

| 格式 | 标准库/工具 |
|------|------------|
| YAML | `PyYAML` (`yaml.safe_load`) |
| JSON | `json.loads` |
| CSV | `csv.DictReader` |
| TOML | `tomli` / `tomllib` (Python 3.11+) |
| URL query | `urllib.parse.parse_qs` |
| HTML/XML | `BeautifulSoup` / `lxml` |
| Markdown | `markdown-it-py` / `mistune` |

## 如果环境不允许装依赖

**必须有降级方案，且降级方案要明确标注局限性**：

```python
try:
    import yaml
    def parse_frontmatter(text):
        return yaml.safe_load(text)
except ImportError:
    # FALLBACK: 仅支持简单键值和单层列表，不支持嵌套、注释、多行字符串
    def parse_frontmatter(text):
        ...
```

## 防御性检查清单

- [ ] 写解析器前，先搜索是否已有标准库或成熟第三方库
- [ ] 如果必须手写，先写出 10 个边界测试用例
- [ ] 手写解析器的 docstring/注释里必须说明「不支持什么」
- [ ] 永远不要假设输入格式是"固定"的

## 案例

- [[05-Knowledge/Reflections/hermes-coding-blindspots-20260415|Hermes 的 lint.py frontmatter 解析器失误]]
