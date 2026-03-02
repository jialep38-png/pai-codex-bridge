# 260302-codex-direct-usable

## 背景
用户要求“继续，直接可以在 codex 里使用”。在此前高等价运行时基础上，需要进一步降低使用门槛，提供一键启动和环境自检。

## 目标
让用户在项目目录中可直接用单个命令启动 Codex，并自动触发 PAI 生命周期事件；同时提供依赖检查能力。

## 分阶段计划

### Phase 1: 运行时能力扩展
- [x] 增加 `launch-codex` 子命令（自动 SessionStart/Stop/SessionEnd）
- [x] 增加 AGENTS 自动生成能力（可关闭）
- [x] 增加 `doctor` 自检命令

### Phase 2: 启动入口与文档
- [x] 新增 `Codex/runtime/pai-codex.ps1`
- [x] 新增 `Codex/runtime/pai-codex.sh`
- [x] 更新 `Codex/runtime/README.md` 与 `Codex/README.md`

### Phase 3: 测试与验证
- [x] 新增单元测试（运行时依赖收集等）
- [x] 新增集成测试（launch-codex、doctor）
- [x] 执行全量相关测试并通过

## 验证记录
- `py -m unittest discover -s Tools/tests -p "test_pai_codex_runtime_*.py"`（通过，13/13）
- `py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"`（通过，6/6）
- `py -m compileall Tools/pai_codex_runtime.py Tools/codex_bridge_generator.py Tools/tests/test_pai_codex_runtime_unit.py Tools/tests/test_pai_codex_runtime_integration.py Tools/tests/test_codex_bridge_generator.py Tools/tests/test_codex_bridge_integration.py`（通过）

## 关键结论
- 现已具备“直接可用”的启动入口与事件编排能力。
- 当前环境 `doctor` 检测显示缺少 `bun`，会影响 `.ts` hooks 执行（安全关键 pre-tool hook 在缺失 bun 时按阻断处理）。
