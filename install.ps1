# -*- coding: utf-8 -*-
<#
.SYNOPSIS
  将 stock-analysis skill 安装到本地 AI 工具(Claude Code / Cursor / OpenSpec)
.DESCRIPTION
  检测已安装的 AI 工具,自动创建 symlink 或复制文件,实现跨工具加载。
  不修改任何工具的全局配置,只新增指向本 repo 的链接。
#>
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillName = "stock-analysis"
$homeDir = $env:USERPROFILE

Write-Host "=== Stock Analysis Skill 安装 ===" -ForegroundColor Cyan
Write-Host "Repo: $repoRoot`n"

$installed = @()

# 1. Claude Code: ~/.claude/skills/stock-analysis -> repo
$claudeSkills = Join-Path $homeDir ".claude\skills"
$claudeLink = Join-Path $claudeSkills $skillName
if (Test-Path $claudeSkills) {
    if (Test-Path $claudeLink) {
        Write-Host "[Claude Code] 已存在: $claudeLink (跳过)" -ForegroundColor Yellow
    } else {
        try {
            # Windows symlink 需要管理员或开发者模式;失败则回退到 junction
            cmd /c mklink /J "$claudeLink" "$repoRoot" | Out-Null
            if (Test-Path $claudeLink) {
                Write-Host "[Claude Code] ✓ Junction: $claudeLink -> $repoRoot" -ForegroundColor Green
                $installed += "Claude Code"
            }
        } catch {
            Write-Host "[Claude Code] 创建链接失败(需管理员权限): $_" -ForegroundColor Red
            Write-Host "  手动: mklink /J `"$claudeLink`" `"$repoRoot`"" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[Claude Code] 未检测到 ~/.claude/ (跳过)" -ForegroundColor DarkGray
}

# 2. Cursor: .cursor/rules/stock-analysis.md (项目级) 或全局 ~/.cursor/rules/
$cursorRules = Join-Path (Get-Location) ".cursor\rules"
if (-not (Test-Path $cursorRules)) {
    $cursorRules = Join-Path $homeDir ".cursor\rules"
}
if (Test-Path (Split-Path $cursorRules -Parent)) {
    New-Item -ItemType Directory -Path $cursorRules -Force | Out-Null
    $cursorFile = Join-Path $cursorRules "$skillName.md"
    Copy-Item (Join-Path $repoRoot "SKILL.md") $cursorFile -Force
    Write-Host "[Cursor] ✓ 复制: $cursorFile" -ForegroundColor Green
    $installed += "Cursor"
} else {
    Write-Host "[Cursor] 未检测到 .cursor/ (跳过)" -ForegroundColor DarkGray
}

# 3. OpenSpec: AGENTS.md 追加引用 + openspec update
$openspecCmd = Get-Command openspec -ErrorAction SilentlyContinue
$agentsMd = Join-Path (Get-Location) "AGENTS.md"
if ($openspecCmd -or (Test-Path $agentsMd)) {
    $refLine = "- @stock-analysis: $repoRoot/SKILL.md"
    $needAdd = $true
    if (Test-Path $agentsMd) {
        $content = Get-Content $agentsMd -Raw
        if ($content -match "stock-analysis") { $needAdd = $false }
    }
    if ($needAdd) {
        Add-Content -Path $agentsMd -Value "`n$refLine" -Encoding UTF8
        Write-Host "[OpenSpec] ✓ AGENTS.md 追加引用" -ForegroundColor Green
    } else {
        Write-Host "[OpenSpec] AGENTS.md 已含引用 (跳过)" -ForegroundColor Yellow
    }
    if ($openspecCmd) {
        Write-Host "[OpenSpec] 运行 openspec update 刷新..." -ForegroundColor DarkGray
        try { openspec update 2>&1 | Out-Null } catch {}
    }
    $installed += "OpenSpec"
} else {
    Write-Host "[OpenSpec] 未检测到 openspec 命令或 AGENTS.md (跳过)" -ForegroundColor DarkGray
}

Write-Host "`n=== 完成 ===" -ForegroundColor Cyan
if ($installed.Count -gt 0) {
    Write-Host "已安装到: $($installed -join ', ')" -ForegroundColor Green
} else {
    Write-Host "未检测到任何 AI 工具。请先安装 Claude Code / Cursor / OpenSpec 之一。" -ForegroundColor Yellow
}
Write-Host "`n卸载: 删除对应链接/文件即可(repo 不受影响)"
