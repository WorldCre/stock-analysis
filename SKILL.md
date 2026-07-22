---
name: stock-analysis
zh_name: "股票深度分析工作流"
en_name: "Stock Deep Analysis Workflow"
description: "对任意 A股/港股/美股进行全生命周期深度分析,基于 akshare/yfinance 真实历史数据,支持增量更新(RAG),生成交互式 HTML 仪表盘"
category: finance
scenario: investment
aspect_hint: "真实数据 → 树状分析 → 仪表盘 → 增量更新"
featured: 1
tags: ["stock", "analysis", "A股", "港股", "美股", "dashboard", "rag"]
---

# 股票深度分析全流程 Skill

## 概述

基于 akshare/yfinance **真实历史数据**的股票深度分析工具。分析结果以**树状 Markdown**存入 git 仓库,支持**增量更新**(RAG 知识库)——再次分析同一股票只拉新增数据,复用历史数据与分析结论。

## 触发条件

"分析XX股票" / "XX股票走势" / "XX未来会怎样" / "生成XX仪表盘" / "XX估值模型"

## ⚠️ 关键纪律

1. **日期锚定**:执行前读取系统 `currentDate`,所有时点以此为基准
2. **真实数据优先**:价格必须来自 akshare/yfinance,ATH/回撤/Alpha 全部程序计算,禁止编造
3. **RAG 增量**:再次分析前先检查 `analyses/<stock>/data.json` 是否存在,存在则用 `--incremental`
4. **字段保护**:增量重跑只覆盖机器字段,保留 AI 写的分析(.md 文件)

## 工作流

```
Phase 0: 环境准备 + 日期锚定
Phase 1: 真实数据采集 (fetch_and_analyze.py, 支持 --incremental)
Phase 2: 历史走势复盘 (AI 填写 events.md/phases.md/drawdowns.md)
Phase 3: 生成历史仪表盘 (build_dashboards.py)
Phase 4: 未来情景推演 (AI 填写 forecast/*.md)
Phase 5: 生成展望仪表盘
Phase 6 (可选): 深度专题 + PPT
```

## Phase 0: 环境准备

```powershell
pip install -r requirements.txt   # akshare pandas yfinance pyyaml
```

确认股票代码:`sh600690`(A股)/ `hk06690`(港股)/ `usAAPL`(美股)。

## Phase 1: 真实数据采集

```powershell
# 首次分析(全量拉取)
python scripts/fetch_and_analyze.py sh600690 海尔智家 2026-07-22

# 再次分析(增量,只拉新数据) ← RAG 模式
python scripts/fetch_and_analyze.py sh600690 海尔智家 2026-07-22 --incremental

# 强制全量重拉(校正前复权,超6个月建议)
python scripts/fetch_and_analyze.py sh600690 海尔智家 2026-07-22 --force
```

脚本输出到 `analyses/<公司>-<代码>/`:
- `data.json` — 纯机器数据(stats/monthly/annual/compare_series/volume/price_lookup)
- `daily_full.csv` — 原始日线(增量拉取的数据源)
- `drawdowns.md` — 回撤 + Alpha 分解(程序算数据)
- 其余 .md 骨架(待 AI 填写)

### 股东增减持数据(已知缺口,需人工补充)

akshare **无港股/A股股东增减持接口**,且本环境 WebSearch 不联网,无法自动获取大股东减持记录。这是 events.md 事件梳理的已知薄弱点——靠记忆写增减持必然遗漏(如腾讯多次减持快手)。

**权威数据源(需人工查后补入 events.md)**:
- 港股:港交所披露易 https://www1.hkexnews.hk/ → 大股东权益披露(Substantial Shareholder's Interests, SFO Part XV),输入代码查每次5%+持股变动
- A股:巨潮资讯网 http://www.cninfo.com.cn/ → 股东持股变动,或 akshare `stock_ggcg_em`(高管增减持)/`stock_share_change_cninfo`(股本变动)
- 美股:SEC EDGAR Form 4(内部人交易)/ Schedule 13D/13G(5%+大股东)

**处理方式**:events.md 中涉及增减持的节点,price 用 price_lookup 对齐真实价,事件描述标注"以XX披露为准",并在已知遗漏时显式留"待补充"节点(诚实优于编造)。


### 增量机制(RAG)

1. 读 `data.json` 的 `full_fetch_date`,超 6 个月提醒 `--force`
2. 读 `daily_full.csv` 找 `max(date)`
3. 只拉截止日之后的新增数据 → 合并 → 去重
4. 重算机器字段,**保留** annual.event / drawdowns.cause(混合字段)和所有 .md(人工字段)
5. 打印建议 commit message

## Phase 2: 历史走势复盘

AI agent 用 Write 工具填写 `analyses/<stock>/` 下的 .md 文件(格式:YAML frontmatter + 正文):

- `events.md` — 关键节点(20-25个,price 用 data.json 的 price_lookup 对齐真实值)
- `phases.md` — 阶段划分(5-8个)
- (drawdowns.md 已由程序生成,AI 只补 cause)

### .md 文件格式

```markdown
---
type: events
stock: sh600690
updated: 2026-07-22
items:
  - date: 2024-10
    price: 31.65
    title: 历史最高点ATH
    bg: 9·24行情白电暴涨...
---

# 正文(可选)
```

## Phase 3: 历史仪表盘

```powershell
python scripts/build_dashboards.py --stock-dir analyses/海尔智家-sh600690
```
生成 `analyses/<stock>/html/history-zh.html`。含:ECharts 主图(scatter节点可点击+滚轮缩放)、个股 vs 指数对比、成交量、回撤 Alpha 分解、护城河/三好/产业链。

## Phase 4: 未来情景推演

AI 填写 `forecast/*.md`:
- `scenarios.md` — 三情景路径
- `valuation.md` — 5种估值(历史PE/SOTP/斐波那契/Comps/DCF)+ 估值演变
- `catalysts.md` — 催化剂矩阵 + 机构目标价
- `watchpoints.md` — 观测节点 + 策略框架

## Phase 5: 展望仪表盘

`build_dashboards.py` 同步生成 `outlook-zh.html`。

## 基本面分析框架(贯穿 Phase 2/4)

AI 填写 `fundamentals/*.md`,每块含证据+趋势+同业对比+估值含义:
- `moat.md` — 护城河六维(品牌/转换成本/网络效应/成本优势/无形资产/高效规模)
- `three-good.md` — 三好(好行业波特五力 / 好公司DuPont / 好管理资本配置)
- `chain.md` — 产业链(上游/中游/下游/竞争,各含议价权+风险+估值含义)

## RAG 知识库查询

```bash
git log --oneline -- analyses/海尔智家-sh600690/           # 分析过几次
git show HEAD:analyses/海尔智家-sh600690/fundamentals/moat.md  # 上次护城河
git diff HEAD~1 HEAD -- analyses/海尔智家-sh600690/fundamentals/moat.md  # 变化
```

## ✅ 质量检查

- [ ] 当前日期 vs 数据最新日期同一年?
- [ ] ATH/回撤由程序计算(非人工填)?
- [ ] 关键节点 price 用 price_lookup 对齐真实值?
- [ ] 增量模式是否保留了人工 .md 内容?
- [ ] HTML 节点可点击,scatter 事件正常?

## 完成后

```powershell
Start-Process analyses/海尔智家-sh600690/html/history-zh.html
# 按 fetch 脚本打印的提示手动 commit
```

## 多工具加载

```powershell
.\install.ps1    # Windows: 自动适配 Claude Code / Cursor / OpenSpec
./install.sh     # Linux/Mac
```

## 注意事项

1. 价格必须来自 akshare/yfinance 真实数据;财报/事件来自公司公告
2. 同时呈现多空观点,不偏颇
3. 每份输出含免责声明 + 数据截止日
4. 适用市场:A股(akshare最佳)> 港股 > 美股(yfinance)
5. 前复权会因分红送转偏移,`full_fetch_date` 超 6 个月用 `--force` 校正
