## 产品文档
`README.md` - 项目总览、目标、安装与版本演进
`PLATFORM.md` - 平台兼容矩阵与跨平台问题清单
`SECURITY.md` - 公共仓库安全基线与提示注入防护规则

## 前端文档
`Releases/v4.0.1/.claude/PAI-Install/README.md` - 安装器 Web/Electron/CLI 架构与前端交互协议

## 后端文档
`Releases/v4.0.1/.claude/hooks/README.md` - Hook 生命周期、依赖关系与配置规范
`Releases/v4.0.1/.claude/PAI/README.md` - PAI 核心子系统（算法/技能/记忆/通知）说明

## 当前任务文档
（当前无进行中任务）

## 已归档任务文档
`workflow/done/260302-codex-compatibility-bridge.md` - 将 Claude 专用发行内容桥接为 Codex 可用版本（最小可用）
`workflow/done/260302-codex-equivalence-runtime.md` - 构建 Codex 运行时以模拟 Claude Hook 生命周期，追求高等价兼容
`workflow/done/260302-codex-direct-usable.md` - 提供一键启动与 doctor 自检，让 Codex 直接可用
`workflow/done/260302-github-opensource-package-and-report.md` - 产出万字工作总结并封装 GitHub 可上传开源发布包

## 全局重要记忆
- 当前仓库是多版本发布仓库，核心可运行载荷位于 `Releases/*/.claude/`。
- `v4.0.1` 是当前主版本；其他版本用于历史回溯与迁移对照。
- 本仓库原生面向 Claude Code，Codex 适配需通过桥接层实现，不能直接复用 Hook 机制。
