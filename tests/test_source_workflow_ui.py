from rewindpy.report import _REPORT_MESSAGES, HTML_TEMPLATE


def test_report_includes_source_workflow_actions() -> None:
    assert 'id="openSource"' in HTML_TEMPLATE
    assert 'id="copyDiagnostic"' in HTML_TEMPLATE
    assert 'id="copyLocation"' in HTML_TEMPLATE
    assert 'vscode://file/' in HTML_TEMPLATE
    assert 'navigator.clipboard.writeText' in HTML_TEMPLATE
    assert "key === 'o'" in HTML_TEMPLATE
    assert "key === 'c'" in HTML_TEMPLATE
    assert "key === 'l'" in HTML_TEMPLATE


def test_source_workflow_messages_are_bilingual() -> None:
    assert _REPORT_MESSAGES['en']['open_source'] == 'Open source'
    assert _REPORT_MESSAGES['zh']['open_source'] == '打开源码'
    assert _REPORT_MESSAGES['en']['copy_diagnostic'] == 'Copy diagnostic'
    assert _REPORT_MESSAGES['zh']['copy_diagnostic'] == '复制诊断'
