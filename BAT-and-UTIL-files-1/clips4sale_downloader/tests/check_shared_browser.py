"""Local headless check: two clients share a host and own separate tabs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import clip4sale_preview_downloader as d
from playwright.sync_api import sync_playwright

root = Path(tempfile.mkdtemp(prefix='c4sdl-browser-check-'))
d.APP_DATA_ROOT = root
args = SimpleNamespace(profile_dir=root / 'login', browser='chrome')
pool_id = hashlib.sha256((str(args.profile_dir.resolve()) + args.browser).encode()).hexdigest()[:16]
pool = root / 'shared-browsers' / pool_id
profile = pool / 'profile-test'
profile.mkdir(parents=True)
with sync_playwright() as pw:
    host = pw.chromium.launch_persistent_context(str(profile), channel='chrome', headless=True,
                                               args=['--remote-debugging-port=0'])
    try:
        (pool / 'host-test.json').write_text(json.dumps({'profile': profile.name}), encoding='utf-8')
        status = lambda text: print(d.terminal_text(text))
        _, first = d.open_shared_browser_tab(pw, args, status)
        _, second = d.open_shared_browser_tab(pw, args, status)
        first.page.goto('data:text/html,first')
        second.page.goto('data:text/html,second')
        assert len(host.pages) == 3
        extras = [host.new_page() for _ in range(7)]
        assert len(host.pages) == 10
        with patch.object(d, 'browser_executable_for', return_value=None):
            try:
                d.open_shared_browser_tab(pw, args, status)
            except d.DownloadError:
                pass  # Full host correctly proceeds to the new-host path.
            else:
                raise AssertionError('Allocated an eleventh tab in a full host')
        assert len(host.pages) == 10
        for page in extras:
            page.close()
        first.close()
        assert not second.page.is_closed()
        assert second.page.url.endswith('second')
        second.close()
        assert len(host.pages) == 1
        print('Shared host reuse, ten-tab cap and per-client tab cleanup passed')
    finally:
        host.close()
