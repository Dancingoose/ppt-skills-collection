"""Resolve a local Chromium-family browser for HTML-to-PPTX rendering."""
import os
from pathlib import Path


def candidate_executables():
    """Return explicitly configured and conventional local browser paths."""
    candidates = []
    configured = os.environ.get("PPT_PLAYWRIGHT_EXECUTABLE", "").strip()
    if configured:
        candidates.append(Path(configured))
    if os.name == "nt":
        roots = [os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES")]
        for root in filter(None, roots):
            candidates.extend((
                Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe",
            ))
    return [candidate for index, candidate in enumerate(candidates) if candidate.is_file() and candidate not in candidates[:index]]


def launch_browser(playwright, **options):
    """Launch bundled Chromium first, then a compatible locally installed browser.

    Returns ``(browser, runtime_name)`` so callers can record which runtime
    rendered the deck. An explicitly configured executable takes precedence
    over conventional Edge and Chrome paths after bundled Chromium fails.
    """
    try:
        return playwright.chromium.launch(**options), "playwright-chromium"
    except Exception as bundled_error:
        fallback_errors = []
        for executable in candidate_executables():
            try:
                browser = playwright.chromium.launch(executable_path=str(executable), **options)
                return browser, str(executable)
            except Exception as exc:
                fallback_errors.append(f"{executable}: {exc}")
        details = "\n".join(fallback_errors)
        raise RuntimeError(
            "No usable Chromium-family browser. Install Playwright Chromium or set "
            "PPT_PLAYWRIGHT_EXECUTABLE to a compatible local browser. "
            f"Bundled launch error: {bundled_error}" + (f"\nFallback errors:\n{details}" if details else "")
        ) from bundled_error
