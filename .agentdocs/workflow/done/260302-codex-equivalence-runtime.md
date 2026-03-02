# 260302-codex-equivalence-runtime

## 背景
用户要求将 PAI 在 Codex 中尽量还原至接近 Claude Code 原生体验。此前已完成最小桥接（AGENTS 生成），但缺少 Hook 生命周期自动化。

## 目标
构建一套 Codex 运行时兼容层，尽可能模拟 Claude Hook 事件流：
- SessionStart / SessionEnd
- PreToolUse / PostToolUse
- Stop

并允许复用现有 Hook 脚本（优先 TypeScript hook），实现可执行、可测试、可扩展。

## 范围
- 新增运行时核心：配置加载、事件模型、Hook 调度、执行器
- 新增 CLI 入口：用于手动/脚本化触发各类事件
- 新增示例配置与使用文档
- 新增单元测试与集成测试

## 非目标
- 不修改 Codex 内核
- 不保证所有 Claude 私有载荷字段 100% 一致
- 不实现 Claude statusLine 内嵌能力（以外部运行时替代）

## 分阶段计划

### Phase 1: 任务治理与架构设计
- [x] 创建任务文档并登记索引
- [x] 定义事件模型与配置格式

### Phase 2: 运行时实现
- [x] 实现 HookRunner（按事件读取配置并调度）
- [x] 实现 HookExecutor（跨脚本类型执行与超时控制）
- [x] 实现 CLI 命令（session-start/session-end/pre-tool/post-tool/stop）
- [x] 新增 `run-bash` 命令，自动触发 pre/post-tool

### Phase 3: 测试与验证
- [x] 单元测试（配置解析、事件匹配、命令构建）
- [x] 集成测试（临时目录 + 假 Hook 脚本执行）
- [x] 本地验证执行通过

### Phase 4: 文档收口
- [x] 补充 Codex Runtime 使用文档
- [x] 更新索引与任务状态
- [x] 评估是否归档 done

## 风险
- 部分 Hook 脚本依赖 Bun/Claude 特定上下文，需降级处理或显式提示。
- Windows 环境下脚本可执行权限和 shebang 行为不同，需统一用显式解释器调用。
- 高等价仍受 Codex 无内核 Hook 接口限制，需通过外部事件驱动规避。

## 验证记录
- `py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"`（通过，6/6）
- `py -m unittest discover -s Tools/tests -p "test_pai_codex_runtime_*.py"`（通过，10/10）
- `py -m compileall Tools/pai_codex_runtime.py Tools/codex_bridge_generator.py Tools/tests/test_codex_bridge_generator.py Tools/tests/test_codex_bridge_integration.py Tools/tests/test_pai_codex_runtime_unit.py Tools/tests/test_pai_codex_runtime_integration.py`（通过）
