# PAI Codex Runtime

## 目标
在 Codex 环境中模拟 Claude Hook 生命周期，以尽量复用 `Releases/v4.0.1/.claude/settings.json` 中定义的 hooks。

## 支持事件
- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `Stop`
- `SessionEnd`

## 命令入口
- Windows: `Codex/runtime/pai-runtime.ps1`
- POSIX: `Codex/runtime/pai-runtime.sh`
- 直接调用: `py Tools/pai_codex_runtime.py ...`
- 一键启动 Codex（推荐）:
  - Windows: `Codex/runtime/pai-codex.ps1`
  - POSIX: `Codex/runtime/pai-codex.sh`

## 基础示例

```powershell
# 环境自检（先跑这个）
py Tools/pai_codex_runtime.py doctor

# 1) 会话开始
py Tools/pai_codex_runtime.py session-start --project-root .

# 2) 工具调用前（可阻断）
py Tools/pai_codex_runtime.py pre-tool --tool-name Bash --tool-input-json '{"command":"ls"}' --json

# 3) 工具调用后
py Tools/pai_codex_runtime.py post-tool --tool-name Bash --tool-input-json '{"command":"ls"}'

# 4) 生成回复后
py Tools/pai_codex_runtime.py stop

# 5) 会话结束
py Tools/pai_codex_runtime.py session-end
```

自动 pre/post 包装执行（推荐）：

```powershell
py Tools/pai_codex_runtime.py run-bash --command-text "git status" --project-root .
```

一键启动 Codex（自动 SessionStart/Stop/SessionEnd）：

```powershell
# 当前目录作为项目根目录
.\Codex\runtime\pai-codex.ps1

# 透传 codex 参数
.\Codex\runtime\pai-codex.ps1 --model gpt-5.3-codex
```

## 配置来源
默认读取：`Releases/v4.0.1/.claude/settings.json`

可自定义：

```powershell
py Tools/pai_codex_runtime.py --settings <path/to/settings.json> --pai-dir <path/to/.claude> session-start
```

## 阻断语义
`pre-tool` 事件下，出现以下情况会返回退出码 `2`：
- Hook 返回码为 `2`
- Hook JSON 输出中 `decision` 为 `deny/block/blocked`
- 关键 Hook（`SecurityValidator`/`AgentExecutionGuard`/`SkillGuard`）超时或执行失败

## 已知限制
- 仍然属于外部运行时模拟，不是 Codex 内核原生 Hook。
- `statusLine` 无法内嵌到 Codex UI，只能外部呈现。
- 依赖 Bun 的 `.ts` Hook 需要系统可用 `bun`；若无 Bun 会降级失败并给出错误。

## 依赖建议
- Python 3（已用 `py` 调用）
- Codex CLI（`doctor` 会检查）
- Bun（若需执行 `.ts` Hook，强烈建议安装）
