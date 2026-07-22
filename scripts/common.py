# -*- coding: utf-8 -*-
"""共享路径解析与工具检测(可移植,无硬编码路径)"""
import os
import re


def get_repo_root():
    """返回 git repo 根目录(scripts/ 的上一级)"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def safe_name(name):
    """将公司名转为文件系统安全的名(去掉 \\ / : * ? " < > |)"""
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def get_stock_dir(code, name):
    """根据代码+公司名返回 analyses/<公司>-<代码>/ 路径"""
    return os.path.join(get_repo_root(), "analyses", f"{safe_name(name)}-{code}")


def resolve_stock_dir(stock_dir=None, code=None, name=None):
    """解析股票目录:优先 --stock-dir,否则从 code+name 推导"""
    if stock_dir:
        return os.path.abspath(stock_dir)
    if code and name:
        return get_stock_dir(code, name)
    raise ValueError("需要提供 --stock-dir 或 code+name")


def detect_ai_tools(project_root=None):
    """检测当前环境可用的 AI 工具,返回 dict"""
    project_root = project_root or get_repo_root()
    home = os.path.expanduser("~")
    tools = {}

    # Claude Code: ~/.claude/skills/
    claude_skills = os.path.join(home, ".claude", "skills")
    tools["claude"] = os.path.isdir(claude_skills)

    # Cursor: 项目根 .cursor/ 或全局 ~/.cursor/
    tools["cursor"] = os.path.isdir(os.path.join(os.getcwd(), ".cursor")) or \
                      os.path.isdir(os.path.join(home, ".cursor"))

    # OpenSpec: openspec 命令可用 或 AGENTS.md 存在
    import shutil
    tools["openspec"] = shutil.which("openspec") is not None or \
                        os.path.isfile(os.path.join(os.getcwd(), "AGENTS.md"))

    return tools


def format_bytes(n):
    """字节数转人类可读"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"
