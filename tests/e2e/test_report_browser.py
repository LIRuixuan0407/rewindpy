from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from rewindpy.demos import create_demo_report

pytestmark = pytest.mark.e2e


def _launch_chromium(playwright):
    try:
        return playwright.chromium.launch(headless=True)
    except Exception as first_error:
        for command in ("chromium", "chromium-browser", "google-chrome"):
            executable = shutil.which(command)
            if executable:
                return playwright.chromium.launch(
                    headless=True,
                    executable_path=executable,
                )
        if os.environ.get("REWINDPY_REQUIRE_BROWSER_E2E") == "1":
            raise first_error
        pytest.skip(f"Chromium is not installed for Playwright: {first_error}")


def test_multi_file_report_browser_workflow(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    report = create_demo_report(
        "multi-file",
        output=tmp_path / "multi-file.html",
        language="en",
    )
    console_errors: list[str] = []
    page_errors: list[str] = []

    with sync_api.sync_playwright() as playwright:
        browser = _launch_chromium(playwright)
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.set_content(report.read_text(encoding="utf-8"), wait_until="load")

        page.locator("#code .code-line").first.wait_for(state="visible")
        assert page.locator("#fileTree .file-item").count() == 3
        assert page.locator("#code .code-line").count() > 1
        assert "app.py" in page.locator("#fileName").inner_text()

        page.keyboard.press("Control+p")
        page.locator("#quickOpenInput").fill("config")
        page.locator("#quickOpenResults .palette-result").first.click()
        assert "config_loader.py" in page.locator("#fileName").inner_text()

        page.keyboard.press("Control+f")
        page.locator("#sourceSearchInput").fill("json")
        assert page.locator("mark.search-match").count() >= 1
        page.keyboard.press("Escape")

        page.keyboard.press("Control+Shift+f")
        page.locator("#globalSearchInput").fill("StartupError")
        page.locator("#globalSearchResults .palette-result").first.click()
        assert "service.py" in page.locator("#fileName").inner_text()

        page.locator("#exceptionsTab").click()
        assert page.locator("#tabBody .exception-node").count() == 3
        page.locator("#tabBody .exception-node").last.click()
        assert "config_loader.py" in page.locator("#fileName").inner_text()

        initial_step = page.locator("#stepText").inner_text()
        page.locator("#prev").click()
        assert page.locator("#stepText").inner_text() != initial_step

        page.locator("#languageToggle").click()
        assert "源代码" in page.locator("#sourceTitle").inner_text()
        page.locator("#themeToggle").click()
        assert page.locator("html").get_attribute("data-theme") == "light"

        browser.close()

    assert page_errors == []
    assert console_errors == []
