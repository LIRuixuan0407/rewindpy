from rewindpy.report import HTML_TEMPLATE


def test_report_renders_compressed_cycle_metadata():
    assert "event.repeat_count" in HTML_TEMPLATE
    assert "event.step_end" in HTML_TEMPLATE
    assert "report_trimmed_events" in HTML_TEMPLATE

