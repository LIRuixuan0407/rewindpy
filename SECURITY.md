# Security policy / 安全策略

## Reporting / 报告漏洞

Use GitHub private vulnerability reporting. Do not open a public issue containing credentials, private crash reports, or exploitable details.

请使用 GitHub 私密漏洞报告。不要在公开 Issue 中提交凭据、私人崩溃报告或可被利用的细节。

## Runtime-data safety / 运行时数据安全

Reports may include source lines, local values, file names, and exception details. RewindPy generates reports locally and redacts common secret names, but users must still review every report before sharing.

报告可能包含源码、局部变量、文件名和异常信息。RewindPy 在本地生成报告并遮挡常见敏感名称，但用户在分享前仍须人工检查。

Security-sensitive changes must preserve:

- No automatic upload or network transmission / 不自动上传或联网传输
- Bounded events and captured value sizes / 限制事件数量和捕获值大小
- Common secret-name redaction / 常见敏感名称脱敏
- Explicit user action before sharing / 分享前需要用户明确操作
