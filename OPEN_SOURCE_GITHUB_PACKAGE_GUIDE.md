# GitHub 开源封装与发布指南

## 目标

把当前仓库整理为“可直接上传到 GitHub”的开源发布包，并生成本地 `dist` 产物用于备份和分发。

## 已生成产物

执行封装后将产生：

1. `dist/github-upload/Personal_AI_Infrastructure-main/`（可直接上传目录）
2. `dist/Personal_AI_Infrastructure-main-github-opensource.zip`（压缩包）

## 封装规则

封装目录默认包含项目完整内容，并排除以下本地构建产物：

1. `dist/`
2. `__pycache__/`
3. `.pytest_cache/`
4. `*.pyc`
5. `*.pyo`

## 本地检查建议

上传前建议至少执行：

```powershell
py Tools/pai_codex_runtime.py doctor --json
py -m unittest discover -s Tools/tests -p "test_codex_bridge*.py"
py -m unittest discover -s Tools/tests -p "test_pai_codex_runtime_*.py"
```

## GitHub 上传步骤

1. 在 GitHub 创建空仓库（建议不勾选初始化 README）。
2. 将 `dist/github-upload/Personal_AI_Infrastructure-main/` 中全部内容上传到仓库根目录。
3. 或者直接上传 zip 后在本地解压再推送。
4. 发布首个 Release 时，建议在说明中引用 `OPEN_SOURCE_WORK_SUMMARY_20260302.md` 作为阶段说明。

## 建议仓库设置

1. 开启 Issues 与 Discussions。
2. 启用分支保护（至少保护 `main`）。
3. 打开 Security alerts（Dependabot / secret scanning）。
4. 在仓库首页固定以下文档：
   - `README.md`
   - `Codex/README.md`
   - `Codex/runtime/README.md`
   - `CONTRIBUTING.md`

