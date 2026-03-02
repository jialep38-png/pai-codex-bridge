# 260302-codex-compatibility-bridge

## 背景
用户希望把当前 PAI（Personal AI Infrastructure）仓库改造成 Codex 可用版本。现有仓库主发布内容高度依赖 Claude Code 的 `settings.json + hooks + CLAUDE.md` 机制，无法直接在 Codex 中等价运行。

## 目标
在不破坏现有 Claude 版本结构的前提下，提供一个 **Codex 最小可用桥接层**，让用户可在 Codex 工作流中复用 PAI 的核心文档、算法与技能信息架构。

## 范围
- 新增 Codex 兼容文档与安装/生成工具
- 生成可直接用于 Codex 项目的 `AGENTS.md`（或等效文件）
- 明确不兼容项（Claude Hooks、StatusLine、特定工具匹配器）

## 非目标
- 不做 Claude Hook 到 Codex 的 1:1 运行时迁移
- 不改动历史 Releases 的已有行为
- 不覆盖用户现有 `~/.codex` 或 `~/.claude` 配置

## 分阶段计划

### Phase 1: 文档与任务治理
- [x] 初始化 `.agentdocs/index.md`
- [x] 创建任务文档并登记到索引

### Phase 2: Codex 兼容桥接实现
- [x] 新增 Codex 兼容目录与说明文档
- [x] 新增桥接生成脚本（从仓库结构生成 Codex 指令文件）
- [x] 生成示例输出并校验路径有效性

### Phase 3: 测试与验证
- [x] 增加单元测试（脚本核心函数）
- [x] 增加集成测试（临时目录生成与结果检查）
- [x] 执行本地测试并记录结果

### Phase 4: 回顾与收口
- [x] 更新本任务 TODO 状态
- [x] 判断是否归档到 `workflow/done/`
- [x] 更新 `.agentdocs/index.md` 的当前任务列表

## 技术决策（进行中）
- 采用“桥接层”而非“硬迁移”：保留原 `.claude` 发布载荷，新增 `Codex/` 目录与生成器。
- 使用 Python 标准库实现生成工具与测试，避免新增第三方依赖。

## 风险
- Codex 与 Claude 的生命周期事件机制不同，无法零改动复用 hooks。
- 若用户已有严格本地 AGENTS 规范，需明确合并策略，避免覆盖冲突。

## 验证记录
- 单元+集成测试：`py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"`（通过，6/6）
- 语法检查：`py -m compileall Tools/codex_bridge_generator.py Tools/tests/test_codex_bridge_generator.py Tools/tests/test_codex_bridge_integration.py`（通过）
