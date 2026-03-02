# Codex 兼容层（PAI Bridge）

这个目录提供 PAI 的 Codex 兼容方案，分为两层：
- 静态桥接层：生成项目级 `AGENTS.md`
- 运行时层：模拟 Claude Hook 生命周期

## 目标
在保留原有 Claude 版本发布结构的同时，让 PAI 的核心内容（算法、技能、上下文路由）可以在 Codex 工作流中直接使用。

## 快速开始
在仓库根目录执行：

```powershell
py Tools/codex_bridge_generator.py --project-root . --output AGENTS.md --force
```

执行后会生成项目级 `AGENTS.md`，将 PAI 核心路径与技能分类注入到 Codex 指令中。

## Hook 运行时（高等价模式）

运行时入口位于：
- `Codex/runtime/pai-runtime.ps1`（Windows）
- `Codex/runtime/pai-runtime.sh`（POSIX）
- `Tools/pai_codex_runtime.py`（直接调用）
- `Codex/runtime/pai-codex.ps1` / `Codex/runtime/pai-codex.sh`（一键启动 Codex + 生命周期）

示例：

```powershell
py Tools/pai_codex_runtime.py doctor
py Tools/pai_codex_runtime.py session-start --project-root .
py Tools/pai_codex_runtime.py pre-tool --tool-name Bash --tool-input-json '{"command":"ls"}' --json
py Tools/pai_codex_runtime.py run-bash --command-text "git status" --project-root .
py Tools/pai_codex_runtime.py stop
py Tools/pai_codex_runtime.py session-end

# 一键启动 codex（自动触发 session hooks）
.\Codex\runtime\pai-codex.ps1
```

## 生成参数
- `--project-root`: 目标项目目录（默认当前目录）
- `--output`: 输出文件名（默认 `AGENTS.md`）
- `--release`: PAI 发布目录（默认 `Releases/v4.0.1/.claude`）
- `--template`: 模板路径（默认 `Codex/templates/AGENTS.pai-codex.template.md`）
- `--force`: 覆盖已有输出文件

## 兼容性边界
当前桥接层明确不包含以下能力：
- Codex 内核原生 Hook 自动触发（当前通过外部 runtime 模拟）
- Claude `statusLine` 内嵌渲染
- Claude 私有事件字段的 100% 完整复制

## 验证
使用以下命令运行单元测试与集成测试：

```powershell
py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"
```
