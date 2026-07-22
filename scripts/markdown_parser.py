# -*- coding: utf-8 -*-
"""
YAML frontmatter Markdown 解析器
==============================
每个分析 .md 文件格式:
---
type: moat
stock: sh600690
updated: 2026-07-22
items:
  - dim: 品牌
    strength: 强
---
# 正文(可选)
"""
import os
import yaml


def read_md(path):
    """读取 .md 文件,返回 (frontmatter_dict, body_str)"""
    if not os.path.exists(path):
        return {}, ""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}
    body = parts[2].lstrip("\n")
    return frontmatter, body


def write_md(path, frontmatter, body=""):
    """写入 .md 文件(frontmatter + body)"""
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        f.write("---\n\n")
        f.write(body)


def read_items(path, key="items"):
    """便捷:读取 .md 的 items 列表"""
    fm, _ = read_md(path)
    return fm.get(key, [])


def read_meta(path):
    """便捷:读取 .md 的 frontmatter(不含 body)"""
    fm, _ = read_md(path)
    return fm


def update_items(path, items, preserve_body=True, extra_meta=None):
    """更新 .md 的 items,保留 body 和其他 frontmatter 字段"""
    fm, body = read_md(path)
    fm[key := "items"] = items
    if extra_meta:
        fm.update(extra_meta)
    write_md(path, fm, body if preserve_body else "")


def load_analysis_dir(stock_dir):
    """加载整个股票分析目录,返回结构化 dict 供 build_dashboards 用"""
    result = {
        "events": [],
        "phases": [],
        "drawdowns": [],
        "scenarios": {},
        "valuation_floor": [],
        "catalysts": {"upside": [], "downside": []},
        "watchpoints": [],
        "strategy_framework": [],
        "moat": [],
        "three_good": {},
        "chain": {},
        "valuation_evolution": [],
    }

    def p(*args):
        return os.path.join(stock_dir, *args)

    # 顶层 .md
    result["events"] = read_items(p("events.md"))
    result["phases"] = read_items(p("phases.md"))
    # drawdowns: items 含程序数据, frontmatter 可能有 summary
    dd_fm, _ = read_md(p("drawdowns.md"))
    result["drawdowns"] = dd_fm.get("items", [])
    result["drawdowns_summary"] = dd_fm.get("summary", "")

    # forecast/
    sc_fm, _ = read_md(p("forecast", "scenarios.md"))
    result["scenarios"] = sc_fm.get("scenarios", {})
    result["scenarios_meta"] = {k: v for k, v in sc_fm.items() if k != "scenarios"}
    result["valuation_floor"] = read_items(p("forecast", "valuation.md"))
    result["valuation_evolution"] = read_items(p("forecast", "valuation.md"), "evolution")
    cat_fm, _ = read_md(p("forecast", "catalysts.md"))
    result["catalysts"] = cat_fm.get("catalysts", {"upside": [], "downside": []})
    result["watchpoints"] = read_items(p("forecast", "watchpoints.md"))
    result["strategy_framework"] = read_items(p("forecast", "watchpoints.md"), "strategy")

    # fundamentals/
    result["moat"] = read_items(p("fundamentals", "moat.md"))
    tg_fm, _ = read_md(p("fundamentals", "three-good.md"))
    result["three_good"] = tg_fm.get("three_good", {})
    result["three_good_verdict"] = tg_fm.get("verdict", "")
    ch_fm, _ = read_md(p("fundamentals", "chain.md"))
    result["chain"] = ch_fm.get("chain", {})

    return result


if __name__ == "__main__":
    # 自测
    import tempfile
    td = tempfile.mkdtemp()
    test = os.path.join(td, "test.md")
    write_md(test, {"type": "moat", "items": [{"dim": "品牌", "strength": "强"}]}, "# 测试\n正文")
    fm, body = read_md(test)
    print("frontmatter:", fm)
    print("body:", body[:20])
    print("items:", read_items(test))
    print("✓ markdown_parser 自测通过")
