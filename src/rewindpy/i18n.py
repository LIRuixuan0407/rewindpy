from __future__ import annotations

import locale
import os
from typing import Final

SUPPORTED_LANGUAGES: Final = ("en", "zh")

_MESSAGES: Final[dict[str, dict[str, str]]] = {
    "en": {
        "cli_description": "Run Python code and create a rewindable local crash report.",
        "lang_help": "Interface language: auto, en, or zh (may appear anywhere)",
        "run_help": "Run a Python script under RewindPy",
        "target_help": "Path to the Python script",
        "output_help": "HTML report output path",
        "max_events_help": "Maximum number of execution events to retain",
        "open_help": "Open the report in a browser",
        "demo_help": "Generate a built-in crash report",
        "demo_kind_help": "Built-in demo scenario",
        "doctor_help": "Check whether RewindPy is ready to run",
        "json_help": "Print machine-readable JSON",
        "demo_report": "RewindPy demo report: {path}",
        "captured_crash": "RewindPy captured the crash: {path}",
        "target_not_found": "Target script not found: {path}",
        "unknown_demo": "Unknown demo: {kind}",
        "demo_failed": "The demo did not produce a crash report.",
        "invalid_language": "Unsupported language {value!r}. Choose auto, en, or zh.",
        "missing_language": "--lang requires auto, en, or zh.",
        "doctor_title": "RewindPy doctor",
        "doctor_status": "Status",
        "doctor_ready": "READY",
        "doctor_not_ready": "NOT READY",
        "doctor_python": "Python",
        "doctor_platform": "Platform",
        "doctor_virtualenv": "Virtual environment",
        "doctor_supported": "Supported Python",
        "doctor_writable": "Working directory writable",
        "doctor_demo": "Built-in demo smoke test",
        "yes": "yes",
        "no": "no",
        "pass": "PASS",
        "fail": "FAIL",
        "missing_key_title": "Missing key traced",
        "missing_key_summary": "Key {key!r} disappeared from {variable} {distance} {step_word} before the crash.",
        "missing_key_rename": " It may have been renamed to {replacement!r}.",
        "none_title": "None value traced",
        "none_summary_through": "{variable!r} received None through {upstream!r}. {producer}() returned None {distance} {step_word} before the crash.",
        "none_summary_from": "{variable!r} received None from {producer}() {distance} {step_word} before the crash.",
        "none_summary_became": "{variable!r} became None {distance} {step_word} before the crash.",
        "step_singular": "step",
        "step_plural": "steps",
    },
    "zh": {
        "cli_description": "运行 Python 代码，并在崩溃后生成可倒带的本地报告。",
        "lang_help": "界面语言：auto、en 或 zh（可放在命令任意位置）",
        "run_help": "使用 RewindPy 运行 Python 脚本",
        "target_help": "Python 脚本路径",
        "output_help": "HTML 报告输出路径",
        "max_events_help": "最多保留的执行事件数量",
        "open_help": "在浏览器中打开报告",
        "demo_help": "生成内置崩溃演示报告",
        "demo_kind_help": "内置演示场景",
        "doctor_help": "检查 RewindPy 是否可以正常运行",
        "json_help": "输出机器可读的 JSON",
        "demo_report": "RewindPy 演示报告：{path}",
        "captured_crash": "RewindPy 已捕获崩溃：{path}",
        "target_not_found": "找不到目标脚本：{path}",
        "unknown_demo": "未知演示：{kind}",
        "demo_failed": "演示没有生成崩溃报告。",
        "invalid_language": "不支持语言 {value!r}。请选择 auto、en 或 zh。",
        "missing_language": "--lang 后需要填写 auto、en 或 zh。",
        "doctor_title": "RewindPy 环境诊断",
        "doctor_status": "状态",
        "doctor_ready": "可正常运行",
        "doctor_not_ready": "尚未就绪",
        "doctor_python": "Python",
        "doctor_platform": "平台",
        "doctor_virtualenv": "虚拟环境",
        "doctor_supported": "Python 版本受支持",
        "doctor_writable": "当前目录可写",
        "doctor_demo": "内置演示冒烟测试",
        "yes": "是",
        "no": "否",
        "pass": "通过",
        "fail": "失败",
        "missing_key_title": "已追踪缺失键来源",
        "missing_key_summary": "键 {key!r} 在崩溃前 {distance} 步从 {variable} 中消失。",
        "missing_key_rename": " 它可能被重命名为 {replacement!r}。",
        "none_title": "已追踪 None 来源",
        "none_summary_through": "{variable!r} 通过 {upstream!r} 接收到 None。{producer}() 在崩溃前 {distance} 步返回了 None。",
        "none_summary_from": "{variable!r} 从 {producer}() 接收到 None，发生在崩溃前 {distance} 步。",
        "none_summary_became": "{variable!r} 在崩溃前 {distance} 步变成了 None。",
        "step_singular": "步",
        "step_plural": "步",
    },
}


def normalize_language(value: str | None) -> str:
    if value is None or value.strip().lower() == "auto":
        return detect_language()
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"zh", "zh-cn", "zh-hans", "cn", "chinese"}:
        return "zh"
    if normalized in {"en", "en-us", "en-gb", "english"}:
        return "en"
    raise ValueError(value)


def detect_language() -> str:
    explicit = os.environ.get("REWINDPY_LANG")
    if explicit and explicit.strip().lower() != "auto":
        try:
            return normalize_language(explicit)
        except ValueError:
            pass

    candidates = [
        os.environ.get("LC_ALL"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
    ]
    try:
        candidates.append(locale.getlocale()[0])
    except ValueError:
        pass

    for candidate in candidates:
        if candidate and candidate.lower().replace("_", "-").startswith("zh"):
            return "zh"
    return "en"


def text(language: str, message_key: str, **values: object) -> str:
    message = _MESSAGES.get(language, _MESSAGES["en"]).get(message_key, message_key)
    return message.format(**values)
