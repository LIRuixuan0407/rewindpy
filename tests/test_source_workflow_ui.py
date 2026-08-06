from rewindpy.report import HTML_TEMPLATE


def test_report_exposes_source_workflow_actions():
    assert 'id="openSource"' in HTML_TEMPLATE
    assert 'id="copyDiagnostics"' in HTML_TEMPLATE
    assert 'vscode://file/' in HTML_TEMPLATE
    assert "key === 'j'" in HTML_TEMPLATE
    assert "key === 'k'" in HTML_TEMPLATE
    assert "key === 'o'" in HTML_TEMPLATE
    assert "key === 'c'" in HTML_TEMPLATE
