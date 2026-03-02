# Personal AI Infrastructure（中文说明）

> 语言版本： [English (Primary)](README.md) | **中文**

本文件是 `README.md` 的中文配套说明，便于中文用户快速理解项目定位与使用方式。

`README.md` 仍然是项目主文档（英文优先、信息最完整）。

## 项目定位

PAI（Personal AI Infrastructure）是一个面向个人/团队的 AI 基础设施项目，目标是让 AI 从“单次问答工具”升级为“可持续学习、可迭代改进”的长期系统。

当前仓库在保留原有 PAI 结构的基础上，补充了 **Codex 兼容桥接层**，支持在 Codex 环境中复用 PAI 的核心方法与运行时流程。

## 你可以得到什么

1. 结构化的 PAI 方法论（算法、上下文路由、技能体系）
2. 可在 Codex 中直接使用的桥接入口
3. 基于外部 runtime 的 Claude 生命周期模拟能力
4. 一键启动脚本与依赖自检工具

## Codex 快速开始（中文）

在项目根目录执行：

```powershell
# 1) 环境自检
py Tools/pai_codex_runtime.py doctor --json

# 2) 生成/刷新 AGENTS（建议执行）
py Tools/codex_bridge_generator.py --project-root . --output AGENTS.md --force

# 3) 一键启动 Codex + PAI runtime
.\Codex\runtime\pai-codex.ps1
```

## 自动模式（你当前已经启用）

若 PowerShell profile 中存在 `PAI CODEX MODE` 代码块，则直接运行：

```powershell
codex
```

会自动：

1. 进入 PAI runtime 模式
2. 注入 `--dangerously-bypass-approvals-and-sandbox`

若要绕过包装层，使用：

```powershell
codex-raw
```

## 关键文档导航

1. [Codex 兼容层总览](Codex/README.md)
2. [Codex Runtime 详细说明](Codex/runtime/README.md)
3. [开源封装与发布指南](OPEN_SOURCE_GITHUB_PACKAGE_GUIDE.md)
4. [完整阶段总结（万字）](OPEN_SOURCE_WORK_SUMMARY_20260302.md)
5. [贡献指南](CONTRIBUTING.md)
6. [支持与反馈](SUPPORT.md)

## 兼容边界说明

当前方案属于“高等价兼容”，不是 Codex 内核原生 Hook。大多数核心流程可运行，但部分 transcript 相关 hook 在收尾阶段可能出现非阻断日志噪音。

## 许可与来源

- 本项目采用 MIT License
- 当前仓库基于原有 PAI 项目结构进行扩展与适配
- 请在二次分发时保留原始许可证与署名信息
