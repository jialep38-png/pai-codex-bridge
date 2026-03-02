# PAI Codex Bridge v0.1

这是面向 Codex 的最小可用桥接版本。

## 包含内容
- `AGENTS.sample.md`：由 `Tools/codex_bridge_generator.py` 生成的示例指令文件。

## 用法
1. 在你的目标项目根目录执行：

```powershell
py <this-repo>/Tools/codex_bridge_generator.py --project-root . --output AGENTS.md --force
```

2. 启动 Codex 后，项目级 `AGENTS.md` 将生效。

## 设计原则
- 不破坏原有 `Releases/v4.0.1/.claude` 结构。
- 不强行迁移 Claude Hook 运行时。
- 优先复用 PAI 的算法、技能与上下文路由文档。

## 已知限制
- 无 Claude Hook 自动触发（SessionStart/PreToolUse/Stop）。
- 无 Claude 状态栏集成。
- 需要通过显式命令触发相关工具脚本。
