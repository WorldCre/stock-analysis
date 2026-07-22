#!/usr/bin/env bash
# 将 stock-analysis skill 安装到本地 AI 工具(Claude Code / Cursor / OpenSpec)
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="stock-analysis"
HOME_DIR="$HOME"

echo "=== Stock Analysis Skill 安装 ==="
echo "Repo: $REPO_ROOT"
echo ""

INSTALLED=()

# 1. Claude Code: ~/.claude/skills/stock-analysis -> repo
CLAUDE_SKILLS="$HOME_DIR/.claude/skills"
CLAUDE_LINK="$CLAUDE_SKILLS/$SKILL_NAME"
if [ -d "$CLAUDE_SKILLS" ]; then
    if [ -e "$CLAUDE_LINK" ]; then
        echo "[Claude Code] 已存在: $CLAUDE_LINK (跳过)"
    else
        ln -s "$REPO_ROOT" "$CLAUDE_LINK"
        echo "[Claude Code] ✓ symlink: $CLAUDE_LINK -> $REPO_ROOT"
        INSTALLED+=("Claude Code")
    fi
else
    echo "[Claude Code] 未检测到 ~/.claude/ (跳过)"
fi

# 2. Cursor: .cursor/rules/stock-analysis.md
CURSOR_RULES="$(pwd)/.cursor/rules"
if [ ! -d "$(dirname "$CURSOR_RULES")" ]; then
    CURSOR_RULES="$HOME_DIR/.cursor/rules"
fi
if [ -d "$(dirname "$CURSOR_RULES")" ] || [ -d "$HOME_DIR/.cursor" ]; then
    mkdir -p "$CURSOR_RULES"
    cp "$REPO_ROOT/SKILL.md" "$CURSOR_RULES/$SKILL_NAME.md"
    echo "[Cursor] ✓ 复制: $CURSOR_RULES/$SKILL_NAME.md"
    INSTALLED+=("Cursor")
else
    echo "[Cursor] 未检测到 .cursor/ (跳过)"
fi

# 3. OpenSpec: AGENTS.md + openspec update
AGENTS_MD="$(pwd)/AGENTS.md"
if command -v openspec &>/dev/null || [ -f "$AGENTS_MD" ]; then
    REF_LINE="- @stock-analysis: $REPO_ROOT/SKILL.md"
    if [ -f "$AGENTS_MD" ] && grep -q "stock-analysis" "$AGENTS_MD"; then
        echo "[OpenSpec] AGENTS.md 已含引用 (跳过)"
    else
        echo "" >> "$AGENTS_MD"
        echo "$REF_LINE" >> "$AGENTS_MD"
        echo "[OpenSpec] ✓ AGENTS.md 追加引用"
    fi
    if command -v openspec &>/dev/null; then
        echo "[OpenSpec] 运行 openspec update 刷新..."
        openspec update 2>/dev/null || true
    fi
    INSTALLED+=("OpenSpec")
else
    echo "[OpenSpec] 未检测到 openspec (跳过)"
fi

echo ""
echo "=== 完成 ==="
if [ ${#INSTALLED[@]} -gt 0 ]; then
    echo "已安装到: ${INSTALLED[*]}"
else
    echo "未检测到任何 AI 工具。请先安装 Claude Code / Cursor / OpenSpec 之一。"
fi
echo ""
echo "卸载: 删除对应链接/文件即可(repo 不受影响)"
