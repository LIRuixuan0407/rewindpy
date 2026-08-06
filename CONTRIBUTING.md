# Contributing / 参与贡献

RewindPy is intentionally focused: it records bounded, project-local execution history and explains where crash-causing values originated.

RewindPy 保持聚焦：记录有数量上限的项目内执行历史，并解释导致崩溃的数值来自哪里。

## Development setup / 开发环境

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
rewindpy doctor
```

## Before a pull request / 提交 PR 前

1. Explain the concrete debugging problem. / 说明要解决的具体调试问题。
2. Add a minimal failing example or test first. / 优先添加最小失败示例或测试。
3. Preserve local-only reports, redaction, truncation, and event bounds. / 保持本地报告、脱敏、截断和事件上限。
4. Preserve Python 3.10 compatibility. / 保持 Python 3.10 兼容。
5. Update both English and Chinese user-facing text. / 同步更新中英文用户界面和文档。

## Good first contributions / 适合首次贡献

- Reproducible crash examples / 可复现的崩溃示例
- False-positive or false-negative analysis tests / 误报或漏报测试
- Report accessibility and keyboard navigation / 报告可访问性和键盘导航
- Bilingual documentation improvements / 中英文文档改进
- Performance improvements backed by measurements / 有测量数据支撑的性能优化
