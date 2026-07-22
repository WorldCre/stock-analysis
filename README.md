# Stock Analysis Skill

A股/港股/美股 全生命周期深度分析工具。基于 akshare/yfinance **真实历史数据**,生成交互式 HTML 仪表盘(历史走势 + 未来展望),含护城河/三好框架/产业链/Alpha 分解等深度分析。

## 特性

- 📊 **真实数据驱动**:akshare(A股/港股)+ yfinance(美股)拉取前复权日线,ATH/回撤/Alpha 全部程序计算
- 🔄 **RAG 知识库**:分析结果 + 原始数据进 git,再次分析同一股票只拉增量数据
- 🌳 **树状分析结构**:每个分析维度独立 .md 文件,git 追溯友好
- 📈 **ECharts 仪表盘**:个股 vs 指数对比、成交量、关键节点点击、回撤 Alpha 分解
- 🔧 **多工具适配**:Claude Code / Cursor / OpenSpec 自动加载

## 快速开始

```powershell
# 1. Clone
git clone git@github.com:WorldCre/stock-analysis.git
cd stock-analysis

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装到 AI 工具(Claude Code / Cursor / OpenSpec)
.\install.ps1

# 4. 分析一只股票
python scripts/fetch_and_analyze.py sh600690 海尔智家 2026-07-22
# (AI agent 填写各 .md 分析文件)
python scripts/build_dashboards.py --stock-dir analyses/海尔智家-sh600690

# 5. 查看仪表盘
Start-Process analyses/海尔智家-sh600690/html/history-zh.html
```

## 代码结构

```
stock-analysis/
├── SKILL.md                       # Skill 定义(AI 工具读取)
├── install.ps1 / install.sh       # 多工具自动适配
├── scripts/
│   ├── common.py                  # 路径解析
│   ├── markdown_parser.py         # YAML frontmatter 解析
│   ├── fetch_and_analyze.py       # 数据抓取(支持 --incremental 增量)
│   └── build_dashboards.py        # HTML 仪表盘生成
└── analyses/                      # RAG 知识库
    └── <公司>-<代码>/
        ├── data.json              # 纯机器数据(每次重跑覆盖)
        ├── daily_full.csv         # 原始日线(增量拉取的数据源)
        ├── events.md              # 关键节点
        ├── phases.md              # 阶段划分
        ├── drawdowns.md           # 回撤 + Alpha 分解
        ├── forecast/              # 三情景/估值/催化剂/观测节点
        ├── fundamentals/          # 护城河/三好/产业链
        └── html/                  # 最终仪表盘
```

## RAG 知识库

每次分析的结果都提交到 `analyses/` 目录。再次分析同一股票时,`--incremental` 模式:

1. 读取已有 `daily_full.csv`,找到最后日期
2. 只拉取截止日之后的新增数据(而非全量历史)
3. 合并数据,重算统计字段
4. **保留** AI 写的分析内容(events/phases/forecast/fundamentals)

### 增量更新

```powershell
# 首次分析(全量拉取)
python scripts/fetch_and_analyze.py sh600690 海尔智家 2026-07-22

# 再次分析(增量,只拉新数据)
python scripts/fetch_and_analyze.py sh600690 海尔智家 2026-07-22 --incremental
```

### 历史查询

```bash
# 这支股票分析过几次?
git log --oneline -- analyses/海尔智家-sh600690/

# 上次的护城河评估
git show HEAD:analyses/海尔智家-sh600690/fundamentals/moat.md

# 两次分析间护城河变了什么
git diff HEAD~1 HEAD -- analyses/海尔智家-sh600690/fundamentals/moat.md
```

> ⚠️ 前复权数据会因分红送转而回溯调整。`data.json` 记录 `full_fetch_date`,
> 距今超 6 个月时脚本会提醒全量重拉(`--force`)以校正历史价格。

## 已分析股票

| 股票 | 代码 | 最后分析 | 数据截止 |
|------|------|---------|---------|
| 海尔智家 | sh600690 | 2026-07-22 | 2026-07-21 |

## 免责声明

价格数据为 akshare/yfinance 真实历史数据;财报/事件/机构观点为公开信息整理;情景推演与目标价为分析估算。仅供研究参考,不构成投资建议。
