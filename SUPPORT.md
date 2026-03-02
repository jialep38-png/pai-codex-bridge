# 支持与反馈（Support）

## 使用问题

若你在使用中遇到问题，建议按以下顺序处理：

1. 先阅读：
   - `README.md`
   - `Codex/README.md`
   - `Codex/runtime/README.md`
2. 在项目根目录执行依赖自检：

```powershell
py Tools/pai_codex_runtime.py doctor --json
```

3. 复现时附上最小命令与关键日志片段，再提交 Issue。

## 建议反馈格式

请尽量包含：

1. 操作系统与终端（PowerShell/pwsh/bash）
2. 执行命令
3. 实际结果与期望结果
4. 是否安装 `bun` 与 `codex`
5. `doctor --json` 输出（可脱敏）

## 安全问题

如涉及安全漏洞（例如命令注入、权限绕过、敏感信息泄露），请不要公开披露细节。建议先参考 `SECURITY.md` 的流程进行私下报告。

## 贡献改进

欢迎通过 PR 改进文档、测试和兼容性问题。提交前请阅读 `CONTRIBUTING.md`。

