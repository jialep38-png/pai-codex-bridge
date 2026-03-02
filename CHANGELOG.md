# 变更记录（Changelog）

本文件记录面向 Codex 兼容与可用化改造的关键变更。

## 2026-03-02

### 新增

1. 新增 Codex 桥接生成器：`Tools/codex_bridge_generator.py`
2. 新增 Codex 运行时：`Tools/pai_codex_runtime.py`
3. 新增一键启动脚本：
   - `Codex/runtime/pai-codex.ps1`
   - `Codex/runtime/pai-codex.sh`
4. 新增运行时文档与桥接文档：
   - `Codex/README.md`
   - `Codex/runtime/README.md`
5. 新增开源协作文档：
   - `CONTRIBUTING.md`
   - `CODE_OF_CONDUCT.md`
   - `SUPPORT.md`
6. 新增完整阶段总结文档：
   - `OPEN_SOURCE_WORK_SUMMARY_20260302.md`

### 改进

1. 通过外部 runtime 模拟 Claude 生命周期事件：
   - `SessionStart`
   - `PreToolUse`
   - `PostToolUse`
   - `Stop`
   - `SessionEnd`
2. 增加 `doctor` 与 `launch-codex` 能力，提升可用性。
3. 完成 Windows 下可执行解析、编码输出与参数透传修复。

### 配置

1. 已在 PowerShell 与 Windows PowerShell profile 注入 `codex` 接管函数。
2. 运行 `codex` 时自动注入：
   - `--dangerously-bypass-approvals-and-sandbox`
3. 保留 `codex-raw` 作为原生命令入口。

### 验证

1. 桥接相关测试通过：
   - `py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"`
2. 运行时相关测试通过：
   - `py -m unittest discover -s Tools/tests -p "test_pai_codex_runtime_*.py"`
3. 依赖自检通过：
   - `py Tools/pai_codex_runtime.py doctor --json`

