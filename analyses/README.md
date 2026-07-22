# analyses/ — RAG 知识库

每只股票一个目录,命名 `<公司名>-<代码>`(如 `海尔智家-sh600690`)。

## 目录结构

```
<公司>-<代码>/
├── data.json          # 纯机器数据: stats/monthly/annual/compare_series/volume/price_lookup
├── daily_full.csv     # 原始前复权日线(增量拉取的数据源)
├── events.md          # 关键节点(YAML frontmatter)
├── phases.md          # 阶段划分
├── drawdowns.md       # 回撤 + Alpha 分解(个股 vs 指数)
├── forecast/
│   ├── scenarios.md   # 三情景路径
│   ├── valuation.md   # 5种估值方法
│   ├── catalysts.md   # 催化剂矩阵
│   └── watchpoints.md # 观测节点 + 策略框架
├── fundamentals/
│   ├── moat.md        # 护城河六维
│   ├── three-good.md  # 三好框架(波特五力+DuPont)
│   └── chain.md       # 产业链与竞争格局
└── html/
    ├── history-zh.html
    └── outlook-zh.html
```

## 字段保护策略(增量重跑时)

| 类型 | 文件 | 策略 |
|------|------|------|
| 纯机器 | data.json | 每次覆盖 |
| 混合 | drawdowns.md (cause/type) | 数据重算,文案保留 |
| 纯人工 | events/phases/forecast/fundamentals | 从不自动覆盖 |

## .md 文件格式

每个分析文件用 YAML frontmatter 存结构化数据,正文存人类可读分析:

```markdown
---
type: moat
stock: sh600690
updated: 2026-07-22
items:
  - dim: 品牌
    strength: 强
    evidence: ...
---

# 正文(可选,详细展开)
```

`build_dashboards.py` 通过 `scripts/markdown_parser.py` 解析 frontmatter 渲染 HTML。
