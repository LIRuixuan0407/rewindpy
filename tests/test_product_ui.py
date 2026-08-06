from rewindpy.report import _REPORT_MESSAGES, HTML_TEMPLATE


def test_report_has_product_workspace() -> None:
    for marker in (
        'class="workspace"',
        'id="codeScroll"',
        'id="variablesTab"',
        'id="stackTab"',
        'id="play"',
        'id="themeToggle"',
        'id="languageToggle"',
    ):
        assert marker in HTML_TEMPLATE


def test_report_has_interactive_workflow() -> None:
    assert "function togglePlay" in HTML_TEMPLATE
    assert "function renderCode" in HTML_TEMPLATE
    assert "function renderVariables" in HTML_TEMPLATE
    assert "function renderStack" in HTML_TEMPLATE
    assert "event.code==='Space'" in HTML_TEMPLATE
    assert "key === 'o'" in HTML_TEMPLATE
    assert "key === 'c'" in HTML_TEMPLATE
    assert "key === 'l'" in HTML_TEMPLATE


def test_product_ui_messages_are_bilingual() -> None:
    assert _REPORT_MESSAGES["en"]["variables"] == "Variables"
    assert _REPORT_MESSAGES["zh"]["variables"] == "变量"
    assert _REPORT_MESSAGES["en"]["call_stack"] == "Call stack"
    assert _REPORT_MESSAGES["zh"]["call_stack"] == "调用栈"
