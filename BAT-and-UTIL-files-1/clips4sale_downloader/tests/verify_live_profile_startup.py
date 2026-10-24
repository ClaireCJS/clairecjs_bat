"""Validate concurrent startup using an existing profile and an offline page.

Creates unique workspace artifacts, prints no cookie values, and never closes
or modifies the original browser window. Run with the source profile path.
"""
from pathlib import Path
import json
import sys
import time
import uuid

import clip4sale_preview_downloader as downloader


def main():
    from playwright.sync_api import sync_playwright

    sys.stdout.reconfigure(encoding="utf-8")
    source = Path(sys.argv[1]).resolve()
    root = Path.cwd() / ("live-startup-check-" + uuid.uuid4().hex[:10])
    root.mkdir()
    started = time.monotonic()
    log = lambda message: print(message, flush=True)
    profile = downloader.clone_concurrent_profile(source, root / "profile", log)
    downloader.preserve_login_snapshot(root / "preferred", profile, log)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), channel="chrome", headless=True, timeout=30_000,
        )
        try:
            context.route("**/*", lambda route: route.fulfill(
                content_type="text/html", body="<title>Offline startup check</title><p>Ready</p>"))
            page = downloader.run_page(context)
            downloader.goto(page, "https://example.invalid/c4sdl-startup-check", headless=True)
            assert page.title() == "Offline startup check"
            cookies = context.cookies()
            site_count = sum(cookie["domain"].lstrip(".").endswith("clips4sale.com")
                             for cookie in cookies)
            result = {"source": str(source), "profile": str(profile),
                      "cookie_count": len(cookies), "site_cookie_count": site_count,
                      "navigated_to": page.url, "elapsed_seconds": round(time.monotonic() - started, 2)}
        finally:
            context.close()
    report = downloader.write_new_json(root / "startup-check.json", result)
    print(json.dumps(result, indent=2))
    print(f"Validation report: {report}")


if __name__ == "__main__":
    main()
