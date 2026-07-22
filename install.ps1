# Install stock-analysis skill to local AI tools (Claude Code / Cursor / OpenSpec)
# Detects installed tools and creates symlinks/copies. Does not modify global configs.
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillName = "stock-analysis"
$homeDir = $env:USERPROFILE

Write-Host "=== Stock Analysis Skill Install ===" -ForegroundColor Cyan
Write-Host "Repo: $repoRoot`n"

$installed = @()

# 1. Claude Code: ~/.claude/skills/stock-analysis -> repo (junction, no admin needed)
$claudeSkills = Join-Path $homeDir ".claude\skills"
$claudeLink = Join-Path $claudeSkills $skillName
if (Test-Path $claudeSkills) {
    if (Test-Path $claudeLink) {
        Write-Host "[Claude Code] Already exists: $claudeLink (remove it first to reinstall)" -ForegroundColor Yellow
    } else {
        try {
            cmd /c mklink /J "$claudeLink" "$repoRoot" | Out-Null
            if (Test-Path $claudeLink) {
                Write-Host "[Claude Code] OK junction: $claudeLink -> $repoRoot" -ForegroundColor Green
                $installed += "Claude Code"
            }
        } catch {
            Write-Host "[Claude Code] Failed (needs admin or dev mode): $_" -ForegroundColor Red
            Write-Host "  Manual: mklink /J `"$claudeLink`" `"$repoRoot`"" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[Claude Code] ~/.claude/ not found (skip)" -ForegroundColor DarkGray
}

# 2. Cursor: .cursor/rules/stock-analysis.md
$cursorRules = Join-Path (Get-Location) ".cursor\rules"
if (-not (Test-Path (Split-Path $cursorRules -Parent))) {
    $cursorRules = Join-Path $homeDir ".cursor\rules"
}
if (Test-Path (Split-Path $cursorRules -Parent)) {
    New-Item -ItemType Directory -Path $cursorRules -Force | Out-Null
    $cursorFile = Join-Path $cursorRules "$skillName.md"
    Copy-Item (Join-Path $repoRoot "SKILL.md") $cursorFile -Force
    Write-Host "[Cursor] OK copied: $cursorFile" -ForegroundColor Green
    $installed += "Cursor"
} else {
    Write-Host "[Cursor] .cursor/ not found (skip)" -ForegroundColor DarkGray
}

# 3. OpenSpec: AGENTS.md + openspec update
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
        Write-Host "[OpenSpec] OK AGENTS.md updated" -ForegroundColor Green
    } else {
        Write-Host "[OpenSpec] AGENTS.md already has reference (skip)" -ForegroundColor Yellow
    }
    if ($openspecCmd) {
        Write-Host "[OpenSpec] Running openspec update..." -ForegroundColor DarkGray
        try { openspec update 2>&1 | Out-Null } catch {}
    }
    $installed += "OpenSpec"
} else {
    Write-Host "[OpenSpec] not found (skip)" -ForegroundColor DarkGray
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
if ($installed.Count -gt 0) {
    Write-Host "Installed to: $($installed -join ', ')" -ForegroundColor Green
} else {
    Write-Host "No AI tools detected. Install Claude Code / Cursor / OpenSpec first." -ForegroundColor Yellow
}
Write-Host "`nUninstall: just remove the link/file (repo is unaffected)"
