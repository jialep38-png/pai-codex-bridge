# pai-codex-bridge（中文）

> 语言版本： [English (Primary)](README.md) | **中文**

这是一个基于 PAI（Personal AI Infrastructure）的衍生项目，目标是让 PAI 的核心能力在 Codex 环境中可直接使用。

## 项目目标

1. 在 Codex 中复用 PAI 方法体系。
2. 尽可能保留高等价生命周期行为。
3. 提供可日常使用的启动与自动模式。

## 核心能力

1. Codex 桥接生成器：`Tools/codex_bridge_generator.py`
2. 运行时生命周期编排：`Tools/pai_codex_runtime.py`
3. 一键启动脚本：`Codex/runtime/pai-codex.ps1` / `Codex/runtime/pai-codex.sh`
4. 依赖自检：`doctor`
5. PowerShell 自动模式：`codex` 包装命令 + `codex-raw` 原生命令

## 快速开始

```powershell
# 1) 依赖检查
py Tools/pai_codex_runtime.py doctor --json

# 2) 生成/刷新 AGENTS（建议）
py Tools/codex_bridge_generator.py --project-root . --output AGENTS.md --force

# 3) 一键启动 Codex + PAI runtime
.\Codex\runtime\pai-codex.ps1
```

## 自动模式

若 PowerShell profile 中存在 `PAI CODEX MODE`，直接执行：

```powershell
codex
```

会自动进入 runtime 并附带 `--dangerously-bypass-approvals-and-sandbox`。

如需绕过包装层：

```powershell
codex-raw
```

## 归属与许可

本仓库基于以下上游项目衍生：

- 上游项目：`danielmiessler/Personal_AI_Infrastructure`
- 上游协议：MIT

本仓库已保留原始 MIT 协议文本，并在 `NOTICE` 中说明衍生关系与改造范围。

## 兼容边界

当前方案是外部运行时模拟 Claude 生命周期，不是 Codex 内核原生 Hook。

多数主流程可用，少量 transcript 相关收尾 hook 可能出现非阻断日志告警。
