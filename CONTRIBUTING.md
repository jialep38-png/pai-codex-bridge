# 贡献指南（Contributing）

感谢你参与本项目。

## 贡献方式

1. 先在 Issue 中描述问题或提案，再开始实现。
2. 变更前请同步阅读 `README.md`、`Codex/README.md`、`Codex/runtime/README.md`。
3. 提交内容应尽量聚焦单一目标，避免混合无关改动。

## 提交要求

1. 代码改动需说明动机、设计取舍与风险。
2. 涉及运行时逻辑（`Tools/pai_codex_runtime.py`）时，必须补充验证命令与结果。
3. 涉及桥接生成器（`Tools/codex_bridge_generator.py`）时，必须补充对应测试或说明为什么无需新增测试。
4. 文档变更需更新相关索引或链接，避免失效引用。

## 最低验证清单

在仓库根目录执行：

```powershell
py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"
py -m unittest discover -s Tools/tests -p "test_pai_codex_runtime_*.py"
```

如改动了脚本，还应执行语法检查：

```powershell
py -m compileall Tools
```

## Pull Request 说明模板

请在 PR 描述中至少包含：

1. 变更背景与目标
2. 主要修改点（文件级）
3. 验证命令与结果
4. 已知限制与后续计划（如有）

## 代码风格

1. 保持实现简单清晰，优先复用现有成熟逻辑。
2. 避免引入不必要依赖。
3. 注释应解释“为什么这样做”，而不是重复代码表面含义。

## 安全与合规

若改动涉及：

1. 工具调用前校验（PreToolUse）
2. 命令执行链路
3. 外部脚本执行或环境变量处理

请明确说明安全影响与降级策略。

