# PAI Codex Bridge

## 定位
这是为 Codex 生成的 PAI 桥接指令文件，目标是在不依赖 Claude Hook 机制的前提下，复用 PAI 的核心方法论与知识结构。

## 核心入口
- PAI 根目录: `{{PAI_ROOT}}`
- 算法版本: `{{ALGO_VERSION}}`
- 算法文件: `{{ALGO_FILE}}`
- 上下文路由: `{{CONTEXT_ROUTING}}`
- 系统总览: `{{PAI_README}}`

## 执行顺序
1. 先在 `{{CONTEXT_ROUTING}}` 定位所需上下文文件。
2. 复杂任务按算法文档执行（Observe/Think/Plan/Build/Execute/Verify/Learn）。
3. 优先复用 `skills/` 目录已有流程与工具说明，避免重复实现。

## 可用技能分类（v4.0.1）
{{SKILL_CATEGORIES}}

## Codex 兼容性说明
- 不支持 Claude Code 的 `settings.json` Hook 生命周期触发（SessionStart / PreToolUse / Stop 等）。
- 不支持 Claude 原生 `statusLine` 与工具 matcher 行为。
- 可继续复用：算法文档、技能文档、多数 TypeScript/Python 工具脚本、记忆目录结构。

## 目录约定（建议）
- 项目内长期记忆可放在 `.agentdocs/`。
- 若需 PAI 工作记忆，可按 `MEMORY/WORK`, `MEMORY/LEARNING`, `MEMORY/STATE` 组织。

## 运行建议
- 本桥接层仅做“可用化”而非 1:1 等价迁移。
- 如需深度迁移，请逐项替换 Hook 功能为显式脚本或命令。
