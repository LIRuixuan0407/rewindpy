<div align="center">

[English](README.md) | [简体中文](README.zh-CN.md)

# ⏪ RewindPy

### Python 程序崩溃了？把它倒回去。

一个本地运行的 Python 崩溃后时间旅行调试器。

[![CI](https://github.com/LIRuixuan0407/rewindpy/actions/workflows/ci.yml/badge.svg)](https://github.com/LIRuixuan0407/rewindpy/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/rewindpy.svg)](https://pypi.org/project/rewindpy/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![在线演示](https://img.shields.io/badge/在线-演示-8A2BE2)](https://liruixuan0407.github.io/rewindpy/)

</div>

![RewindPy 演示](docs/assets/rewindpy-demo.gif)

**[打开在线交互报告](https://liruixuan0407.github.io/rewindpy/)**

RewindPy 会记录有数量上限、仅限项目代码的 Python 执行历史。出现未捕获异常后，它会生成一个自包含 HTML 调试工作区，用于查看源码、局部变量、变化、调用栈、异常原因和执行时间线。

## 一分钟体验

```bash
python -m pip install --upgrade rewindpy
rewindpy --lang zh doctor
rewindpy --lang zh demo multi-file --open
```

## v0.2.0 新增能力

- 使用项目式文件资源管理器浏览报告包含的全部源码文件。
- 时间线、调用栈、数值来源和异常链都能跨文件跳转。
- 使用 `Ctrl+P` 打开文件、`Ctrl+F` 搜索当前文件、`Ctrl+Shift+F` 搜索整个报告。
- 展示显式 `raise ... from ...`、隐式异常上下文、`from None`、异常备注和嵌套 traceback。
- 使用 Report Schema v2 和内嵌 SHA-256 摘要校验报告数据。
- 在 CI 中用真实 Chromium 验证报告交互，并持续检查报告生成性能。

## 调试自己的脚本

```bash
rewindpy --lang zh run --open app.py
rewindpy --lang zh run --output crash.html app.py -- --port 8080
```

目标程序崩溃时会保留原本的非零退出码。报告是本地 HTML 文件，不需要额外服务器。

## 报告工作区

报告包含：

- 支持播放、暂停、单步和速度控制的有界执行时间线；
- 完整源码，以及当前行、崩溃行、来源行和搜索匹配高亮；
- 局部变量和每一步的变量变化；
- 可点击的调用栈和异常链；
- 崩溃切片、缺失键来源、可能重命名和 `None` 来源分析；
- 中英文界面、深浅主题、复制诊断信息和 VS Code 源码跳转。

## 内置演示

```bash
rewindpy --lang zh demo none-origin --open
rewindpy --lang zh demo key-error --open
rewindpy --lang zh demo crash-slice --open
rewindpy --lang zh demo exception-chain --open
rewindpy --lang zh demo multi-file --open
```

## pytest 集成

```bash
pytest --rewind
pytest --rewind --rewind-dir reports --rewind-lang zh
```

成功测试不会生成报告。失败报告默认写入 `.rewindpy/`，pytest 原有输出和退出码保持不变。

## 安全追踪

```bash
rewindpy run --max-events 5000 --include src --exclude tests app.py
rewindpy run --max-events 5000 --max-report-mb 10 app.py
```

RewindPy 使用有界环形缓冲区，跳过常见环境和构建目录，压缩重复循环，优先保留与崩溃相关的事件，并记录保留与丢弃统计。

## 命令参考

```text
rewindpy --version
rewindpy --lang auto|en|zh --help
rewindpy doctor [--json]
rewindpy [--lang auto|en|zh] demo [none-origin|key-error|crash-slice|exception-chain|multi-file] [--output FILE] [--open]
rewindpy [--lang auto|en|zh] run SCRIPT [--output FILE] [--max-events N] [--include PATH] [--exclude PATH] [--max-report-mb MB] [--open] [-- ARGS...]
```

## 开发与质量检查

```bash
python -m pip install -e ".[dev,e2e]"
python -m ruff check .
python -m pytest -q
python -m playwright install chromium
REWINDPY_REQUIRE_BROWSER_E2E=1 python -m pytest -q tests/e2e
python benchmarks/report_benchmark.py --events 5000 --iterations 3
python scripts/build_live_demo.py --check
rewindpy doctor
```

更多说明见 [浏览器测试](docs/browser-e2e.md)、[性能基准](docs/performance.md)、[报告格式](docs/report-schema-v2.md)、[异常链](docs/exception-chain.md) 和 [多文件导航](docs/multi-file-navigation.md)。

## 当前范围

RewindPy v0.2.0 面向 Python 3.10+、单线程本地脚本、未捕获异常、pytest 失败，以及被追踪项目根目录下的 Python 文件。

它不是确定性重放工具。目前不会建模异步任务因果关系、多进程、原生扩展、实时断点或不透明对象内部的任意变化。

## 安全说明

崩溃报告可能包含运行时数据。RewindPy 只在本地写入报告，并遮挡名称中包含 `password`、`token`、`secret`、`api_key` 等关键词的变量或字典键。分享报告前仍然需要人工检查。

贡献、安全、发布与版本历史请查看 [CONTRIBUTING.md](CONTRIBUTING.md)、[SECURITY.md](SECURITY.md)、[RELEASING.md](RELEASING.md) 和 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

RewindPy 使用 [MIT 许可证](LICENSE)。
