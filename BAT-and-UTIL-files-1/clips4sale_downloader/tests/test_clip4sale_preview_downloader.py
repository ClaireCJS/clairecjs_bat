"""Offline tests. All browser requests are fulfilled by local fixtures.

Run: .venv\Scripts\python.exe -B -m unittest -v
Test artifacts are retained in a unique test-artifacts folder, never deleted.
"""
from __future__ import annotations
from contextlib import contextmanager, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid

import clip4sale_preview_downloader as d

LISTING = "https://www.clips4sale.com/studio/100/sample/Cat5-test/Page1/recommended/Limit24"


def record(number, title=None, resolution="1080p"):
    return {"clipId": str(number), "id": number, "title": title or f"Sample {number}",
            "producer": 100, "categoryId": 5, "link": f"/studio/100/{number}/sample",
            "resolution": resolution, "studioTitle": "Sample Studio", "category_name": "Test"}


def page_html(payload, body="", extra=""):
    return ('<!doctype html><html><body><h1>Sample Studio</h1>' + body +
            '<script>window.__remixContext = ' + json.dumps(payload) + ';</script>' + extra + '</body></html>')


def listing_html(records, more=False):
    payload = {"state": {"loaderData": {"route": {"studioId": "100", "title": "Sample Studio",
               "clips": records, "categories": [{"id": 5, "name": "Test"}]}}}}
    script = '''<script>
    function add(cards) {
      for (const c of cards) {
        const row = document.createElement('div');
        row.dataset.testid = 'storeClips_' + c.id + '-clip'; row.style.height = '55px';
        const a = document.createElement('a'); a.dataset.testid = 'storeClips_' + c.id + '-clip-link';
        a.href = c.link; a.textContent = c.title; row.appendChild(a);
        document.getElementById('grid').appendChild(row);
      }
    }
    add(window.__remixContext.state.loaderData.route.clips);
    let page = 1, busy = false, done = MORE;
    window.addEventListener('scroll', async () => {
      if (busy || done || scrollY + innerHeight < document.documentElement.scrollHeight - 10) return;
      busy = true; document.getElementById('loader').style.display = 'block';
      const response = await fetch('/api/mock-clips?page=' + (++page));
      const data = await response.json();
      setTimeout(() => {
        add(data.clips); done = !data.has_more; busy = false;
        document.getElementById('loader').style.display = 'none';
      }, 80);
    });
    </script>'''.replace('MORE', 'false' if more else 'true')
    return page_html(payload, '<div id="grid"></div><div id="loader" data-testid="loader" style="display:none">Loading</div>', script)


class QuietPanel:
    def __init__(self):
        self.total = SimpleNamespace(n=0, update=lambda n: None)
        self.status = ""
        self.waits = []
    def log(self, text): pass
    def draw(self): pass
    def close(self): pass
    def set_total(self, *args): pass
    def wait(self, seconds, pump=None): self.waits.append(seconds)


class TerminalPanelTests(unittest.TestCase):
    @contextmanager
    def panel(self, size=(100, 30)):
        class TTY(io.StringIO):
            def isatty(self):
                return True

        stream, logfile = TTY(), io.StringIO()
        dimensions = list(size)
        with patch.object(d.sys, 'stderr', stream), \
                patch.dict(d.os.environ, {'TERM': 'xterm', 'C4SDL_NO_ANSI': '', 'C4SDL_FORCE_ANSI': ''}), \
                patch.object(d.ProgressPanel, '_terminal_size', side_effect=lambda: tuple(dimensions)), \
                patch.object(d.ProgressPanel, 'RESIZE_POLL_SECONDS', .02):
            panel = d.ProgressPanel(logfile)
            try:
                yield panel, stream, logfile, dimensions
            finally:
                panel.close()

    def test_shared_bars_fill_wide_and_narrow_consoles_without_wrapping(self):
        labels = ['🌈 Global', '📥 ' + 'filename {with braces} 日本語 e\u0301 ' * 8,
                  '⏳ Next clip in 12s']
        with self.panel() as (panel, _, _, _):
            self.assertEqual(type(panel.total).__module__, 'clairecjs_utils.claire_progressbar')
            for columns in (1, 2, 7, 18, 30, 80, 120, 240):
                for label in labels:
                    for current, total in ((0, 10), (5, 10), (10, 10), (37, None)):
                        with self.subTest(columns=columns, label=label, current=current, total=total):
                            line = panel._progress_line(label, current, total, columns)
                            self.assertEqual(panel._display_width(line), columns - 1)
                            self.assertNotIn('\n', line)
            wide = panel._progress_line('🌈 Global', 5, 10, 240)
            self.assertGreater(wide.count('━') + wide.count('─'), 180)

    def test_log_message_colours_are_distinct_and_logfile_stays_plain(self):
        messages = ['📥 Saved: file.mp4', '↩️ Already complete: file.mp4', '🔁 Retry 1/1',
                    '⚠️ Media error: missing', '🎬 [2/4] Clip title', '🌐 Opening the browser']
        with self.panel() as (panel, stream, logfile, _):
            colours = []
            for message in messages:
                styled = panel._colour_line(message)
                colours.append(styled.partition('m')[0])
                panel.log(message)
                self.assertIn(styled, stream.getvalue())
                self.assertIn(message, logfile.getvalue())
            self.assertEqual(len(set(colours)), len(messages))
            self.assertNotIn('\x1b', logfile.getvalue())

    def test_resize_watcher_reanchors_idle_panel_without_new_progress(self):
        with self.panel() as (panel, stream, _, dimensions):
            panel.set_total(12)
            for columns, rows in ((180, 50), (70, 50), (60, 15), (20, 3), (120, 30)):
                start = len(stream.getvalue())
                old_rows = panel.rows
                old_fixed = bool(panel.scroll_bottom)
                changed = threading.Event()
                original_flush = stream.flush

                def flushed():
                    original_flush()
                    if (panel.columns, panel.rows) == (columns, rows):
                        changed.set()

                with patch.object(stream, 'flush', side_effect=flushed):
                    dimensions[:] = [columns, rows]
                    self.assertTrue(changed.wait(1), 'Resize was not noticed while the main thread was idle')
                frame = stream.getvalue()[start:]
                self.assertNotIn('\n', frame)
                self.assertNotIn('\x1b7', frame)  # no stale saved cursor across a resize
                if rows >= 5:
                    self.assertIn(f'\x1b[1;{rows - 2}r', frame)
                    self.assertIn(f'\x1b[{rows - 1};1H', frame)
                    self.assertIn(f'\x1b[{rows};1H', frame)
                else:
                    self.assertEqual(panel.scroll_bottom, 0)
                if old_fixed and old_rows < rows:
                    self.assertIn(f'\x1b[{old_rows};1H\x1b[2K', frame)
            worker = panel._resize_thread
        self.assertFalse(worker.is_alive())
        previous = stream.getvalue()
        panel.draw()
        panel.close()
        self.assertEqual(stream.getvalue(), previous)

    def test_output_device_dimensions_override_stale_environment(self):
        stream = SimpleNamespace(fileno=lambda: 47)
        with patch.dict(d.os.environ, {'COLUMNS': '80', 'LINES': '24'}), \
                patch.object(d.os, 'get_terminal_size', return_value=d.os.terminal_size((170, 46))) as probe:
            self.assertEqual(d.ProgressPanel._terminal_size(SimpleNamespace(stream=stream)), (170, 46))
        probe.assert_called_once_with(47)

    def test_redirected_log_output_has_no_ansi_or_resize_worker(self):
        stream, logfile = io.StringIO(), io.StringIO()
        with patch.object(d.sys, 'stdout', stream), patch.object(d.sys, 'stderr', stream), \
                patch.dict(d.os.environ, {'C4SDL_NO_ANSI': '', 'C4SDL_FORCE_ANSI': ''}):
            panel = d.ProgressPanel(logfile)
            try:
                panel.log('✅ Saved: file.mp4')
                self.assertFalse(panel.ansi)
                self.assertIsNone(panel._resize_thread)
            finally:
                panel.close()
        self.assertNotIn('\x1b', stream.getvalue())
        self.assertIn('Saved: file.mp4', stream.getvalue())


    def test_close_unlocks_clears_status_rows_and_scrolls_past_output(self):
        with self.panel(size=(120, 30)) as (panel, stream, _, _):
            panel.set_total(10)
            panel.transfer_progress(1, 10, '📥 file.mp4')
            start = len(stream.getvalue())
            panel.close()
            cleanup = stream.getvalue()[start:]
            self.assertIn('\x1b[0m\x1b[r\x1b[?25h', cleanup)
            self.assertIn('\x1b[29;1H\x1b[2K', cleanup)
            self.assertIn('\x1b[30;1H\x1b[2K', cleanup)
            self.assertTrue(cleanup.endswith('\x1b[30;1H\r\n'))
            self.assertFalse(panel._resize_thread.is_alive())


class LogicTests(unittest.TestCase):
    def test_legacy_filename_uses_current_implementation_and_version(self):
        here = Path(__file__).resolve()
        project_root = here.parent.parent if here.parent.name.casefold() == 'tests' else here.parent
        commands = (
            project_root / 'compatibility.deprecated' / 'clips4sale_downloader.py',
            project_root / 'compatibility' / 'clips4sale_downloader.py',
            project_root / 'clips4sale_downloader.py',
        )
        command = next((candidate for candidate in commands if candidate.is_file()), commands[-1])
        spec = importlib.util.spec_from_file_location('clips4sale_downloader_compatibility_test', command)
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        self.assertIs(legacy.main, d.main)
        result = subprocess.run([d.sys.executable, '-B', str(command), '--version'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(d.VERSION, result.stdout)
        result = subprocess.run([d.sys.executable, '-B', str(command), '--help'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--retry-failures', result.stdout)
        self.assertIn('--close-browser-on-exit', result.stdout)

    def test_quality_edition_matching_and_studio_boundary(self):
        raws = [record(1, "Example (HD)", "720p"), record(2, "example - 4K", "2160p"),
                record(3, "Example part 2", "1080p")]
        clips = [d.Clip.from_raw(r, LISTING) for r in raws]
        other = d.Clip.from_raw({**record(4, "Example"), "link": "/studio/999/4/example"}, LISTING)
        selected, skipped = d.deduplicate([*clips, other])
        self.assertEqual([c.id for c in selected], ["2", "3", "4"])
        self.assertEqual(len(skipped), 1)
        self.assertEqual(d.clean_title("Example (1080p) - MP4"), "Example")
        self.assertEqual(d.quality_score({"screen_size": "1920x1080", "title": "Incorrect 4K"})[0], 1080)

    def test_category_prefix_table_and_full_studio_category_names(self):
        self.assertEqual(d.category_prefix("Small Penis Humiliation"), "sph")
        self.assertEqual(d.category_prefix("Cuckolding - BBC"), "cuck")
        self.assertEqual(d.category_prefix("Chastity"), "ch")
        self.assertEqual(d.clip_category_name("All Categories", {"category_name": "cuckolding"}), "Cuckolding")
        self.assertEqual(d.clip_category_name("Cuckolding", {"category_name": "chastity"}), "Cuckolding")
        clip = d.Clip.from_raw(record(44, "Example"), LISTING)
        self.assertTrue(d.base_name(Path.cwd(), "Studio", "Cuckolding", clip).startswith("Studio - Cuckolding -"))
        self.assertTrue(d.base_name(Path.cwd(), "Studio", "Cuckolding", clip,
                                    include_category_prefix=True).startswith("cuck - Studio - Cuckolding -"))

    def test_category_prefix_option_is_off_by_default(self):
        args = d.parser().parse_args([LISTING])
        self.assertFalse(args.category_prefixes)
        args = d.parser().parse_args([LISTING, '--category-prefixes'])
        self.assertTrue(args.category_prefixes)

    def test_full_studio_category_uses_primary_then_first_and_handles_old_cache(self):
        for listing_category in ('', 'All', 'All Categories', 'AllCategories'):
            with self.subTest(listing_category=listing_category):
                self.assertEqual(d.clip_category_name(listing_category, {
                    'category_name': 'Primary', 'related_category_links': [{'category': 'Secondary'}]}), 'Primary')
                self.assertEqual(d.clip_category_name(listing_category, {
                    'categories': [{'name': 'First'}, {'name': 'Second'}]}), 'First')
                self.assertEqual(d.clip_category_name(listing_category, {
                    'categories': [{'name': 'First'}, {'name': 'Primary', 'isPrimary': True}]}), 'Primary')
                self.assertEqual(d.clip_category_name(listing_category, {
                    'categoryId': 2, 'categories': [{'id': 1, 'name': 'First'}, {'id': 2, 'name': 'Primary'}]}), 'Primary')
                self.assertEqual(d.clip_category_name(listing_category, {
                    'category': ['First', 'Second']}), 'First')
        self.assertEqual(d.clip_category_name('', {'category_link': '/studio/1/name/Cat7-tease-and-denial/Page1'}),
                         'Tease And Denial')
        self.assertEqual(d.clip_category_name('', {'studioCategories': [{'name': 'Wrong studio-wide category'}]}),
                         'Uncategorized')

    def test_login_redirect_still_prompts_without_force_pause(self):
        class Page:
            url = ''
            visits = 0
            def goto(self, url, **kwargs):
                self.visits += 1
                self.url = 'https://www.clips4sale.com/login' if self.visits == 1 else url
                return SimpleNamespace(status=200)
        page = Page()
        with patch('builtins.input', return_value='') as prompt:
            d.goto(page, LISTING, headless=False)
        prompt.assert_called_once()
        self.assertEqual(page.url, LISTING)

    def test_login_redirect_reopens_original_url(self):
        class Page:
            def __init__(self):
                self.url = ""
                self.calls = []
            def goto(self, url, **kwargs):
                self.calls.append(url)
                self.url = "https://www.clips4sale.com/login" if len(self.calls) == 1 else url
                return SimpleNamespace(status=200)
        page = Page()
        with patch('builtins.input', return_value=''):
            d.goto(page, LISTING, headless=False, pause=True)
        self.assertEqual(page.calls, [LISTING, LISTING])

    def test_safe_windows_names(self):
        self.assertEqual(d.safe_filename('CON.txt'), '_CON.txt')
        self.assertEqual(d.safe_filename('A/B: C?  .'), 'A_B_ C_')
        clip = d.Clip.from_raw(record(1, 'A' * 600), LISTING)
        name = d.base_name(Path('C:/short'), 'Studio', 'Category', clip)
        self.assertTrue(name.endswith('[1]'))
        self.assertLessEqual(len(name), 190)

    def test_media_scoped_to_selected_clip_and_all_roles(self):
        current = {**record(1), "customPreviewUrl": "https://cdn.example/preview.mp4",
                   "cdn_preview_link": "https://cdn.example/preview.mp4",
                   "previewUrl": "https://cdn.example/animation.webm",
                   "gifPreviewUrl": "https://cdn.example/animation.gif",
                   "cdn_previewlg_link": "https://cdn.example/large.jpg",
                   "responsiveSrcset": [{"srcSet": "https://cdn.example/extra.jpg 2x"}],
                   "description": '<img src="https://cdn.example/description.jpg">'}
        payload = {"clip": current, "recommendations": [{**record(2), "customPreviewUrl": "https://cdn.example/wrong.mp4"}]}
        assets = d.media_from_raw(d.detail_data(payload, "1"), LISTING)
        self.assertEqual(len(assets), 6)
        self.assertEqual(sum(a.role == 'preview' for a in assets), 1)
        self.assertFalse(any('wrong' in a.url for a in assets))
        selected = d.media_for_download(assets)
        self.assertEqual(len(selected), 5)
        self.assertEqual([a.role for a in selected],
                         ['preview', 'preview-gif', 'thumbnail', 'image-1', 'image-2'])
        self.assertEqual(next(a for a in selected if a.role == 'thumbnail').url,
                         'https://cdn.example/large.jpg')
        self.assertEqual(d.file_extension('https://cdn.example/x.gif', 'video/webm'), '.webm')
        with self.assertRaises(d.DownloadError):
            d.file_extension('https://cdn.example/x.mp4', 'text/html')

    def test_c4s_still_variants_collapse_by_image_family_and_keep_distinct_images(self):
        root = 'https://imagecdn.clips4sale.com/accounts99/54509/clip_images/'
        variants = [
            'previewlg_34252839.jpg', 'thumb_34252839.jpg',
            'square_sm_34252839.jpg', 'square_md_34252839.jpg',
            'rect_sm_34252839.jpg', 'rect_md_34252839.jpg',
            'rect_lrg_34252839.jpg', 'rect_ex_lrg_34252839.jpg',
        ]
        assets = [d.Media(root + name, 'thumbnail' if name.startswith('previewlg_') else 'image')
                  for name in variants]
        assets.extend([
            d.Media(root + 'bonus_800x450.jpg?width=800&quality=90&id=abc', 'image'),
            d.Media(root + 'bonus_1600x900.jpg?width=1600&quality=90&id=abc', 'image'),
            d.Media(root + 'other.jpg', 'image'),
            d.Media(root + 'motion.webm', 'preview-gif'),
            d.Media(root + 'motion.gif', 'preview-gif'),
        ])
        selected = d.media_for_download(assets)
        stills = [media for media in selected if media.role.startswith(('thumbnail', 'image-'))]
        self.assertEqual([media.role for media in stills], ['thumbnail', 'image-1', 'image-2'])
        self.assertEqual(stills[0].url, root + 'previewlg_34252839.jpg')
        self.assertEqual(len(stills[0].alternate_urls), 7)
        self.assertIn('bonus_1600x900.jpg', stills[1].url)
        self.assertEqual(stills[2].url, root + 'other.jpg')
        animations = [media for media in selected if media.role == 'preview-gif']
        self.assertEqual([media.url for media in animations], [root + 'motion.gif'])

    def test_distinct_animations_survive_while_format_and_quality_variants_collapse(self):
        root = 'https://imagecdn.clips4sale.com/animations/'
        assets = [
            d.Media(root + 'teaser_480p.gif', 'preview-gif'),
            d.Media(root + 'teaser_1080p.webm', 'preview-gif'),
            d.Media(root + 'second.webm', 'preview-gif'),
            d.Media(root + 'second.gif', 'preview-gif'),
            d.Media(root + 'third_001.gif', 'preview-gif'),
            d.Media(root + 'third_002.gif', 'preview-gif'),
        ]
        selected = d.media_for_download(assets)
        self.assertEqual([media.role for media in selected],
                         ['preview-gif', 'preview-gif-2', 'preview-gif-3', 'preview-gif-4'])
        self.assertEqual(selected[0].url, root + 'teaser_1080p.webm')
        self.assertEqual(selected[0].alternate_urls, (root + 'teaser_480p.gif',))
        self.assertEqual(selected[1].url, root + 'second.gif')
        self.assertEqual([media.url for media in selected[2:]],
                         [root + 'third_001.gif', root + 'third_002.gif'])

    def test_completed_scope_rescan_prompt_is_numbered_and_defaults_to_saved_cache(self):
        scope = d.listing_scope(LISTING)
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertTrue(d.ask_rescan(scope, '2026-01-11T14:30:00', 'Sample Studio', 'Test',
                                         headless=True, input_fn=lambda _: '2'))
        self.assertIn('completely downloaded as of 2026-01-11', output.getvalue())
        self.assertIn('[1] Use the saved scan', output.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertFalse(d.ask_rescan(scope, '2026-01-11', headless=True,
                                          input_fn=lambda _: '1'))

    def test_headed_windows_rescan_prompt_uses_topmost_yes_no_dialog(self):
        message_box = Mock(return_value=6)
        windows = SimpleNamespace(user32=SimpleNamespace(MessageBoxW=message_box))
        with patch.object(d.os, 'name', 'nt'), patch.object(d.ctypes, 'windll', windows, create=True):
            accepted = d.ask_rescan(d.listing_scope(LISTING), '2026-01-11T14:30:00',
                                    'Sample Studio', 'Test', headless=False)
        self.assertTrue(accepted)
        text, title, flags = message_box.call_args.args[1:]
        self.assertIn('completely downloaded as of 2026-01-11', text)
        self.assertIn(d.VERSION, title)
        self.assertTrue(flags & 0x00040000)  # MB_TOPMOST

    def test_no_destination_default_or_blank_acceptance(self):
        with patch.object(d, 'CLAIRE_PARENT', Path.cwd() / ('absent-parent-' + uuid.uuid4().hex)), \
             patch.object(d, 'DEFAULT_DESTINATION', Path.cwd() / ('absent-' + uuid.uuid4().hex)):
            answers = iter(['', '20', '1'])
            output = io.StringIO()
            with redirect_stdout(output):
                folder = d.select_destination(None, lambda _: next(answers))
            self.assertEqual(folder, Path.cwd())
            self.assertNotIn('Claire default', output.getvalue())
            self.assertIn('Enter alone does not select', output.getvalue())
        with redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            d.select_destination(None, lambda _: '0')

    def test_custom_destination_and_claire_default_are_explicit(self):
        parent = Path.cwd() / ('claire-parent-' + uuid.uuid4().hex)
        custom = Path.cwd() / ('custom-destination-' + uuid.uuid4().hex)
        parent.mkdir()
        try:
            with patch.object(d, 'CLAIRE_PARENT', parent), \
                 patch.object(d, 'DEFAULT_DESTINATION', parent / 'clips4sale_previews'), \
                 patch.dict(d.os.environ, {'USERNAME': 'claire'}, clear=False):
                answers = iter(['2'])
                with redirect_stdout(io.StringIO()):
                    selected = d.select_destination(None, lambda _: next(answers))
                self.assertEqual(selected, parent / 'clips4sale_previews')
                self.assertTrue(selected.is_dir())

            answers = iter(['2', str(custom), 'YES'])
            with patch.object(d, 'CLAIRE_PARENT', Path.cwd() / ('absent-' + uuid.uuid4().hex)), \
                 redirect_stdout(io.StringIO()):
                selected = d.select_destination(None, lambda _: next(answers))
            self.assertEqual(selected, custom)
            self.assertTrue(selected.is_dir())
        finally:
            # Test artifacts are intentionally retained according to the test module contract.
            pass

    def test_terminal_bars_emit_ansi_rainbow_colors_and_emoji(self):
        class TTY(io.StringIO):
            def isatty(self):
                return True
        stream = TTY()
        with patch.object(d.sys, 'stderr', stream), \
             patch.object(d.os, 'name', 'posix'), \
             patch.dict(d.os.environ, {'TERM': 'xterm'}, clear=False), \
             patch.object(d.shutil, 'get_terminal_size', return_value=(100, 30)):
            panel = d.ProgressPanel()
            panel.set_total(4)
            panel.total.update(1)
            panel.wait(0.01)
            panel.close()
        output = stream.getvalue()
        self.assertIn('\x1b[38;2;', output)
        self.assertIn('🌈', output)
        self.assertIn('⏳', output)
        self.assertIn('\x1b[r', output)

    def test_windows_tty_keeps_ansi_when_classic_console_probe_is_unavailable(self):
        class TTY(io.StringIO):
            def isatty(self):
                return True

        stream = TTY()
        with patch.object(d.sys, 'stderr', stream), \
                patch.object(d.os, 'name', 'nt'), \
                patch.dict(d.os.environ, {'TERM': 'dumb'}, clear=False), \
                patch.object(d.shutil, 'get_terminal_size', return_value=(100, 30)):
            panel = d.ProgressPanel()
            panel.set_total(2)
            panel.total.update(1)
            panel.draw()
            panel.close()
        self.assertTrue(panel.ansi)
        self.assertIn('\x1b[38;2;', stream.getvalue())

    def test_concurrent_profile_clone_keeps_login_state_without_locks(self):
        root = Path.cwd() / ('profile-clone-' + uuid.uuid4().hex)
        source = root / 'source'
        target = root / 'target'
        (source / 'Default').mkdir(parents=True)
        (source / 'Default' / 'Preferences').write_text('{"logged_in": true}', encoding='utf-8')
        (source / 'Local State').write_text('{"profile": {}}', encoding='utf-8')
        cookie_db = sqlite3.connect(source / 'Default' / 'Cookies')
        cookie_db.execute('CREATE TABLE session_cookie (value TEXT)')
        cookie_db.execute('INSERT INTO session_cookie VALUES (?)', ('fixture-login-cookie',))
        cookie_db.commit()
        cookie_db.close()
        (source / 'SingletonLock').write_text('live', encoding='utf-8')
        (source / 'Default' / 'Cookies-wal').write_bytes(b'volatile sidecar')
        (source / 'Cache').mkdir()
        d.clone_browser_profile(source, target)
        self.assertEqual((target / 'Default' / 'Preferences').read_text(encoding='utf-8'), '{"logged_in": true}')
        cloned_db = sqlite3.connect(target / 'Default' / 'Cookies')
        self.assertEqual(cloned_db.execute('SELECT value FROM session_cookie').fetchone()[0], 'fixture-login-cookie')
        cloned_db.close()
        self.assertFalse((target / 'SingletonLock').exists())
        self.assertFalse((target / 'Default' / 'Cookies-wal').exists())
        self.assertFalse((target / 'Cache').exists())

    def test_profile_clone_skips_locked_metrics_and_component_cache(self):
        root = Path.cwd() / ('profile-selection-' + uuid.uuid4().hex)
        source, target = root / 'source', root / 'target'
        (source / 'Default').mkdir(parents=True)
        (source / 'Local State').write_text('{}', encoding='utf-8')
        (source / 'Default' / 'Preferences').write_text('{}', encoding='utf-8')
        (source / 'component_crx_cache').mkdir()
        (source / 'component_crx_cache' / 'large-cache').write_bytes(b'not login state')
        metrics = sqlite3.connect(source / 'Default' / 'declarative_performance_observer.db')
        metrics.execute('CREATE TABLE metric (value TEXT)')
        metrics.commit()
        metrics.execute('BEGIN EXCLUSIVE')
        messages = []
        try:
            d.clone_browser_profile(source, target, status=messages.append)
        finally:
            metrics.rollback()
            metrics.close()
        self.assertFalse((target / 'Default' / 'declarative_performance_observer.db').exists())
        self.assertFalse((target / 'component_crx_cache').exists())
        self.assertTrue((target / d.PROFILE_SNAPSHOT_MARKER).is_file())
        self.assertTrue(any('Local State' in message for message in messages))
        self.assertTrue(any('Login-state copy ready' in message for message in messages))

    def test_profile_cookie_snapshot_captures_committed_wal(self):
        root = Path.cwd() / ('profile-wal-' + uuid.uuid4().hex)
        source, target = root / 'source', root / 'target'
        (source / 'Default' / 'Network').mkdir(parents=True)
        cookies = sqlite3.connect(source / 'Default' / 'Network' / 'Cookies')
        cookies.execute('PRAGMA journal_mode=WAL')
        cookies.execute('CREATE TABLE session_cookie (value TEXT)')
        cookies.execute('INSERT INTO session_cookie VALUES (?)', ('fixture-login',))
        cookies.commit()
        try:
            self.assertTrue((source / 'Default' / 'Network' / 'Cookies-wal').exists())
            d.clone_browser_profile(source, target, status=lambda message: None)
        finally:
            cookies.close()
        clone = sqlite3.connect(target / 'Default' / 'Network' / 'Cookies')
        try:
            self.assertEqual(clone.execute('SELECT value FROM session_cookie').fetchone()[0], 'fixture-login')
        finally:
            clone.close()

    def test_locked_cookie_snapshot_times_out_without_publishing_incomplete_login(self):
        root = Path.cwd() / ('profile-timeout-' + uuid.uuid4().hex)
        source, target = root / 'source', root / 'target'
        (source / 'Default' / 'Network').mkdir(parents=True)
        cookies = sqlite3.connect(source / 'Default' / 'Network' / 'Cookies')
        cookies.execute('CREATE TABLE session_cookie (value TEXT)')
        cookies.commit()
        cookies.execute('BEGIN EXCLUSIVE')
        messages = []
        started = d.time.monotonic()
        try:
            with patch.object(d, 'PROFILE_DATABASE_TIMEOUT_SECONDS', .15), \
                    patch.object(d, 'PROFILE_CLONE_TIMEOUT_SECONDS', 2):
                with self.assertRaisesRegex(d.DownloadError, 'Network.*Cookies.*busy'):
                    d.clone_browser_profile(source, target, status=messages.append)
        finally:
            cookies.rollback()
            cookies.close()
        self.assertLess(d.time.monotonic() - started, 2)
        self.assertFalse((target / 'Default' / 'Network' / 'Cookies').exists())
        self.assertFalse((target / d.PROFILE_SNAPSHOT_MARKER).exists())
        self.assertTrue(list(target.rglob('*.part')))

    def test_profile_copy_total_deadline_is_enforced(self):
        root = Path.cwd() / ('profile-budget-' + uuid.uuid4().hex)
        source = root / 'source'
        source.mkdir(parents=True)
        (source / 'Local State').write_text('{}', encoding='utf-8')
        with patch.object(d, 'PROFILE_CLONE_TIMEOUT_SECONDS', 0):
            with self.assertRaisesRegex(d.DownloadError, 'exceeded.*Local State'):
                d.clone_browser_profile(source, root / 'target', status=lambda message: None)

    def test_locked_primary_profile_uses_idle_login_snapshot(self):
        root = Path.cwd() / ('profile-fallback-' + uuid.uuid4().hex)
        primary = root / 'primary'
        (primary / 'Default' / 'Network').mkdir(parents=True)
        (primary / 'Local State').write_text('{}', encoding='utf-8')
        cookies = sqlite3.connect(primary / 'Default' / 'Network' / 'Cookies')
        cookies.execute('CREATE TABLE session_cookie (value TEXT)')
        cookies.execute('INSERT INTO session_cookie VALUES (?)', ('fixture-login',))
        cookies.commit()
        messages = []
        d.preserve_login_snapshot(primary, primary, messages.append)
        cookies.execute('BEGIN EXCLUSIVE')
        try:
            with patch.object(d, 'PROFILE_DATABASE_TIMEOUT_SECONDS', .15):
                target = d.clone_concurrent_profile(primary, root / 'copy', messages.append)
        finally:
            cookies.rollback()
            cookies.close()
        self.assertNotEqual(target, root / 'copy')
        self.assertTrue((root / 'copy').is_dir())  # partial retained
        self.assertTrue(any('Trying saved login' in message for message in messages))
        clone = sqlite3.connect(target / 'Default' / 'Network' / 'Cookies')
        try:
            self.assertEqual(clone.execute('SELECT value FROM session_cookie').fetchone()[0], 'fixture-login')
        finally:
            clone.close()

    def test_clone_refuses_to_overwrite_existing_destination(self):
        root = Path.cwd() / ('profile-preserve-' + uuid.uuid4().hex)
        source, target = root / 'source', root / 'target'
        source.mkdir(parents=True)
        target.mkdir()
        existing = target / 'Local State'
        existing.write_text('preserve me', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            d.clone_browser_profile(source, target, status=lambda message: None)
        self.assertEqual(existing.read_text(encoding='utf-8'), 'preserve me')

    def test_run_page_reuses_persistent_context_initial_blank_page(self):
        class ExistingPage:
            def is_closed(self):
                return False
            def bring_to_front(self):
                pass

        existing = ExistingPage()

        class Context:
            pages = [existing]
            def new_page(self):
                raise AssertionError('a second page should not be created')

        self.assertIs(d.run_page(Context()), existing)

        class EmptyContext:
            pages = []
            def new_page(self):
                return existing

        self.assertIs(d.run_page(EmptyContext()), existing)

    def test_locked_profile_skips_primary_launch_and_starts_isolated_clone(self):
        root = Path.cwd() / ('locked-profile-' + uuid.uuid4().hex)
        profile = root / 'profile'; profile.mkdir(parents=True)
        (profile / 'SingletonLock').write_text('busy', encoding='utf-8')
        calls = []

        class Chromium:
            def launch_persistent_context(self, profile_path, **kwargs):
                calls.append(Path(profile_path))
                return SimpleNamespace(pages=[])

        args = SimpleNamespace(headless=True, browser='chromium',
                               no_persistent_login=False, profile_dir=profile)
        context = d.open_browser_context(SimpleNamespace(chromium=Chromium()), args)
        self.assertEqual(len(calls), 1)
        self.assertNotEqual(calls[0], profile.resolve())
        self.assertTrue(str(calls[0]).startswith(str(profile.parent / d.PROFILE_FALLBACK_ROOT)))
        self.assertIs(context[0], context[1])

    def test_database_claim_deduplicates_same_media_url_across_clip_records(self):
        root = Path.cwd() / ('media-db-' + uuid.uuid4().hex)
        root.mkdir()
        output = root / 'output'; output.mkdir()
        database_path = root / 'clips4sale.db'
        clip_one = d.Clip.from_raw(record(501), LISTING)
        clip_two = d.Clip.from_raw(record(502), LISTING)
        media = d.Media('https://cdn.example/shared-preview.mp4', 'preview')
        first_path = output / 'first.mp4'
        second_path = output / 'second.mp4'
        first = d.DownloadDatabase(database_path)
        second = d.DownloadDatabase(database_path)
        try:
            first.upsert_clip(clip_one)
            second.upsert_clip(clip_two)
            self.assertTrue(first.claim_media(clip_one, media, first_path))
            self.assertFalse(second.claim_media(clip_two, media, second_path))
            first_path.write_bytes(b'complete')
            first.record_success(clip_one, media, {'path': str(first_path), 'bytes': 8})
            self.assertFalse(second.claim_media(clip_two, media, second_path))
            linked = second.successful_media(clip_two, media)
            self.assertIsNotNone(linked)
            self.assertEqual(linked['path'], str(first_path))
            self.assertFalse(second_path.exists())
        finally:
            first.close()
            second.close()

    def test_database_claim_serializes_two_concurrent_claimers(self):
        from concurrent.futures import ThreadPoolExecutor

        root = Path.cwd() / ('media-race-' + uuid.uuid4().hex)
        root.mkdir()
        database_path = root / 'clips4sale.db'
        clip = d.Clip.from_raw(record(504), LISTING)
        media = d.Media('https://cdn.example/race-preview.mp4', 'preview')

        def claim(path):
            database = d.DownloadDatabase(database_path)
            try:
                database.upsert_clip(clip)
                return database.claim_media(clip, media, path)
            finally:
                database.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda number: claim(root / f'{number}.mp4'), (1, 2)))
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 1)

    @unittest.skipUnless(d.os.name == 'nt', 'Windows process-handle regression')
    def test_windows_pid_check_never_signals_live_or_exited_process(self):
        # The child exits normally when its input pipe closes. Guard os.kill
        # so a regression cannot send a real Ctrl+C to the test console.
        with subprocess.Popen([d.sys.executable, '-c',
                               "import sys; print('ready', flush=True); sys.stdin.read()"],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) as child:
            try:
                self.assertEqual(child.stdout.readline().strip(), 'ready')
                with patch.object(d.os, 'kill', side_effect=AssertionError('Liveness must not signal')):
                    self.assertTrue(d.DownloadDatabase._pid_alive(d.os.getpid()))
                    self.assertTrue(d.DownloadDatabase._pid_alive(child.pid))
                    child.communicate('', timeout=10)
                    self.assertFalse(d.DownloadDatabase._pid_alive(child.pid))
            finally:
                if child.poll() is None:
                    child.communicate('', timeout=10)

    @unittest.skipUnless(d.os.name == 'nt', 'Windows process-handle regression')
    def test_windows_inaccessible_owner_is_not_treated_as_dead(self):
        kernel = SimpleNamespace(OpenProcess=Mock(return_value=None),
                                 WaitForSingleObject=Mock(), CloseHandle=Mock())
        with patch.object(d.ctypes, 'WinDLL', return_value=kernel), \
                patch.object(d.os, 'kill', side_effect=AssertionError('Liveness must not signal')):
            for error, alive in ((5, True), (87, False), (8, True)):
                with self.subTest(error=error), patch.object(d.ctypes, 'get_last_error', return_value=error):
                    self.assertEqual(d.DownloadDatabase._pid_alive(123), alive)
        kernel.WaitForSingleObject.assert_not_called()
        kernel.CloseHandle.assert_not_called()

    def test_retry_failure_is_durable_and_keeps_other_workers_out(self):
        root = Path.cwd() / ('retry-ledger-' + uuid.uuid4().hex)
        root.mkdir()
        clip = d.Clip.from_raw(record(505), LISTING)
        media = d.Media('https://cdn.example/retry.mp4', 'preview')
        first = d.DownloadDatabase(root / 'clips4sale.db')
        observer = d.DownloadDatabase(root / 'clips4sale.db')
        try:
            first.upsert_clip(clip)
            self.assertTrue(first.claim_media(clip, media, root / 'retry.mp4'))
            first.record_failure(clip, media, 'HTTP 404', retrying=True)
            row = observer.connection.execute('SELECT * FROM media').fetchone()
            self.assertEqual((row['status'], row['owner_pid'], row['attempts'], row['error']),
                             ('processing', d.os.getpid(), 2, 'HTTP 404'))
            self.assertIn(('100', '505'), observer.failed_clip_ids())
            self.assertFalse(observer.claim_media(clip, media, root / 'duplicate.mp4'))
            first.record_failure(clip, media, 'HTTP 404')
            row = observer.connection.execute('SELECT * FROM media').fetchone()
            self.assertEqual(row['status'], 'failed')
            self.assertIsNone(row['owner_pid'])
            self.assertEqual(row['attempts'], 2)
        finally:
            first.close()
            observer.close()

    def test_abandoned_old_processing_claim_goes_last_but_live_claim_does_not(self):
        root = Path.cwd() / ('abandoned-claims-' + uuid.uuid4().hex)
        root.mkdir()
        database = d.DownloadDatabase(root / 'clips4sale.db')
        clips = [d.Clip.from_raw(record(number), LISTING) for number in (506, 507, 508)]
        try:
            for clip in clips:
                database.upsert_clip(clip)
                database.claim_media(clip, d.Media(f'https://cdn.example/{clip.id}.mp4', 'preview'),
                                     root / f'{clip.id}.mp4')
            # Emulate an old crashed version with no saved error, using a
            # deterministic owner result rather than an arbitrary live PID.
            database.connection.execute('UPDATE media SET owner_pid=123 WHERE clip_id=506')
            with patch.object(database, '_pid_alive', side_effect=lambda pid: pid != 123):
                failed = database.failed_clip_ids()
            self.assertEqual(failed, {('100', '506')})
            self.assertEqual([clip.id for clip in d.failed_last(clips, failed)], ['507', '508', '506'])
        finally:
            database.close()

    def test_completed_listing_cache_round_trips_without_rescraping(self):
        root = Path.cwd() / ('discovery-cache-' + uuid.uuid4().hex)
        root.mkdir()
        database = d.DownloadDatabase(root / 'clips4sale.db')
        clips = [d.Clip.from_raw(record(601), LISTING), d.Clip.from_raw(record(602), LISTING)]
        try:
            database.store_discovery(LISTING, clips, 'Sample Studio', 'Test', scroll_steps=17)
            cached = database.cached_discovery(LISTING)
            self.assertIsNotNone(cached)
            found, studio, category = cached
            self.assertEqual([clip.id for clip in found], ['601', '602'])
            self.assertEqual((studio, category), ('Sample Studio', 'Test'))
            info = database.discovery_cache_info(LISTING)
            self.assertEqual((info['discovered'], info['scroll_steps']), (2, 17))
        finally:
            database.close()

    def test_scope_history_distinguishes_category_from_whole_studio(self):
        root = Path.cwd() / ('scope-history-' + uuid.uuid4().hex)
        root.mkdir()
        database = d.DownloadDatabase(root / 'clips4sale.db')
        category_scope = d.listing_scope(LISTING)
        studio_scope = d.listing_scope(
            'https://www.clips4sale.com/studio/100/sample/Cat0-AllCategories/Page1/Limit24')
        bare_scope = d.listing_scope('https://www.clips4sale.com/studio/100/sample')
        try:
            self.assertEqual(category_scope.key, 'studio:100:category:5')
            self.assertEqual(studio_scope.key, 'studio:100')
            self.assertEqual(bare_scope, studio_scope)
            self.assertIsNone(database.previous_scope_activity(category_scope))
            run_id = database.start_scope_run(category_scope, LISTING, root / 'downloads')
            database.finish_scope_run(run_id, {
                'completed': True, 'dry_run': False, 'studio': 'Sample Studio',
                'category': 'Test', 'discovered': 24, 'selected': 20,
                'clips': [{'files': [{'path': 'one.mp4'}], 'errors': []}], 'errors': [],
            })
            previous = database.previous_scope_activity(category_scope)
            self.assertEqual(previous['status'], 'complete')
            self.assertEqual((previous['discovered'], previous['selected'], previous['files']), (24, 20, 1))
            self.assertEqual(database.completed_scope_activity(category_scope)['run_id'], run_id)
            self.assertIsNone(database.previous_scope_activity(studio_scope))
        finally:
            database.close()

    def test_legacy_import_preserves_run_history_and_rescan_depth(self):
        root = Path.cwd() / ('history-migration-' + uuid.uuid4().hex)
        root.mkdir()
        source_path = root / 'old.db'
        destination_path = root / 'new.db'
        scope = d.listing_scope(LISTING)
        clips = [d.Clip.from_raw(record(901), LISTING)]
        source = d.DownloadDatabase(source_path)
        try:
            source.store_discovery(LISTING, clips, 'Sample Studio', 'Test', scroll_steps=23)
            run_id = source.start_scope_run(scope, LISTING, root / 'downloads')
            source.finish_scope_run(run_id, {
                'completed': True, 'dry_run': False, 'studio': 'Sample Studio',
                'category': 'Test', 'discovered': 1, 'selected': 1,
                'clips': [{'files': [], 'errors': []}], 'errors': [],
            })
        finally:
            source.close()
        destination = d.DownloadDatabase(destination_path)
        try:
            self.assertGreater(destination.merge_legacy(source_path), 0)
            self.assertEqual(destination.completed_scope_activity(scope)['run_id'], run_id)
            self.assertEqual(destination.discovery_cache_info(LISTING)['scroll_steps'], 23)
        finally:
            destination.close()

    def test_history_database_and_reports_live_under_appdata_root(self):
        self.assertEqual(d.PRIVATE_DATABASE_PATH.parent, d.HISTORY_ROOT)
        self.assertEqual(d.PRIVATE_REPORT_ROOT.parent, d.HISTORY_ROOT)
        self.assertEqual(d.HISTORY_ROOT.parent, d.APP_DATA_ROOT)
        self.assertNotEqual(d.HISTORY_ROOT.parent, d.TEMP_PROFILE_ROOT)
        self.assertEqual(d.DEFAULT_PROFILE_DIR.parent, d.APP_DATA_ROOT)

    def test_temporary_login_profile_migrates_once_to_appdata(self):
        root = Path.cwd() / ('profile-appdata-' + uuid.uuid4().hex)
        legacy = root / 'temp' / 'browser-profile'
        target = root / 'appdata' / 'browser-profile'
        (legacy / 'Default' / 'Network').mkdir(parents=True)
        (legacy / 'Local State').write_text('{}', encoding='utf-8')
        (legacy / 'Default' / 'Network' / 'Cookies').write_bytes(b'SQLite login')
        messages = []
        with patch.object(d, 'LEGACY_DEFAULT_PROFILE_DIR', legacy), \
                patch.object(d, 'DEFAULT_PROFILE_DIR', target):
            self.assertTrue(d.migrate_legacy_login_profile(target, messages.append))
            self.assertTrue((target / 'Default' / 'Network' / 'Cookies').is_file())
            self.assertFalse(d.migrate_legacy_login_profile(target, messages.append))
        self.assertTrue(any('AppData' in message for message in messages))

    def test_cleanup_recycles_only_lower_quality_members_of_same_image_family(self):
        root = Path.cwd() / ('variant-cleanup-' + uuid.uuid4().hex)
        root.mkdir()
        database = d.DownloadDatabase(root / 'history.db')
        high = root / 'clip-thumbnail.jpg'
        low = root / 'clip-image-1.jpg'
        distinct = root / 'clip-image-2.jpg'
        high.write_bytes(b'high-quality-image' * 10)
        low.write_bytes(b'low')
        distinct.write_bytes(b'different-image')
        now = database._now()
        rows = [
            ('thumbnail', 'https://assets.example/previewlg_123.jpg', high),
            ('image-1', 'https://assets.example/thumb_123.jpg', low),
            ('image-2', 'https://assets.example/previewlg_999.jpg', distinct),
        ]
        try:
            for role, url, path in rows:
                database.connection.execute(
                    "INSERT INTO media(studio_id, clip_id, role, url, status, path, updated_at) "
                    "VALUES('100', '55', ?, ?, 'success', ?, ?)",
                    (role, url, str(path), now),
                )
            recycled = []
            def recycle(path):
                source = Path(path)
                destination = source.with_name(source.name + '.recycled')
                source.rename(destination)
                recycled.append(source)
            with patch('send2trash.send2trash', side_effect=recycle), redirect_stdout(io.StringIO()):
                result = d.clean_old_variants(database, root, input_fn=lambda _prompt: '2')
            self.assertEqual(recycled, [low])
            self.assertEqual(result['recycled'], [str(low.resolve())])
            self.assertTrue(high.is_file())
            self.assertTrue(distinct.is_file())
            status = database.connection.execute(
                "SELECT status FROM media WHERE role='image-1'"
            ).fetchone()[0]
            self.assertEqual(status, 'recycled-old-variant')
        finally:
            database.close()

    def test_database_backup_is_verified_and_history_is_read_only(self):
        root = Path.cwd() / ('database-backup-' + uuid.uuid4().hex)
        root.mkdir()
        path = root / 'history.db'
        database = d.DownloadDatabase(path)
        scope = d.listing_scope(LISTING)
        try:
            run_id = database.start_scope_run(scope, LISTING, root)
            database.finish_scope_run(run_id, {
                'completed': True, 'dry_run': False, 'studio': 'Sample Studio',
                'category': 'Test', 'discovered': 9, 'selected': 8,
                'clips': [{'files': [{'path': 'one.mp4'}], 'errors': []}], 'errors': [],
            })
        finally:
            database.close()
        backup = d.automatic_database_backup(path)
        self.assertTrue(backup.is_file())
        with sqlite3.connect(backup) as copied:
            self.assertEqual(copied.execute('PRAGMA quick_check').fetchone()[0], 'ok')
        before = path.stat().st_mtime_ns
        output = io.StringIO()
        with redirect_stdout(output):
            d.print_history(5, path)
        self.assertEqual(path.stat().st_mtime_ns, before)
        self.assertIn('Sample Studio - Test', output.getvalue())
        self.assertIn('found 9; selected 8; files 1; errors 0', output.getvalue())

    def test_cached_rescan_boundary_requires_a_streak(self):
        cached = {str(number) for number in range(1, 8)}
        self.assertEqual(d.longest_consecutive_cached(['1', '100', '101', '2'], cached), 1)
        self.assertEqual(d.longest_consecutive_cached(['1', '100', '2', '3', '4', '5', '6'], cached), 5)

    def test_windows_completion_notification_is_topmost(self):
        message_box = Mock(return_value=1)
        windll = SimpleNamespace(user32=SimpleNamespace(MessageBoxW=message_box))
        with patch.object(d.os, 'name', 'nt'), patch.object(d.ctypes, 'windll', windll, create=True):
            self.assertTrue(d.notify_completion(Path(r'C:\downloads'), 0))
        args = message_box.call_args.args
        self.assertIn('Download run complete', args[1])
        self.assertTrue(args[3] & 0x00040000)

    def test_failed_clips_are_queued_after_pending_clips(self):
        clips = [d.Clip.from_raw(record(number), LISTING) for number in (701, 702, 703)]
        queued = d.failed_last(clips, {('100', '702')})
        self.assertEqual([clip.id for clip in queued], ['701', '703', '702'])

    def test_already_downloaded_video_has_no_inter_clip_wait(self):
        args = SimpleNamespace(dry_run=False, page_delay=2.0, fallback_wait=30.0)
        self.assertEqual(d.inter_clip_wait(True, False, [12.0], False, args), 0.0)
        with patch.object(d, 'random_delay', return_value=3.14):
            self.assertEqual(d.inter_clip_wait(False, True, [], False, args), 3.14)
            self.assertEqual(d.inter_clip_wait(False, False, [], False, args, True), 3.14)

    def test_dry_run_still_uses_requested_page_delay(self):
        args = SimpleNamespace(dry_run=True, page_delay=2.0, fallback_wait=30.0)
        self.assertEqual(d.inter_clip_wait(True, False, [12.0], False, args), 2.0)

    def test_run_log_uses_shared_log_directory(self):
        root = Path.cwd() / ('logs-' + uuid.uuid4().hex)
        with patch.object(d, 'LOG_DIRECTORY', root):
            path, handle = d.open_run_log()
        try:
            self.assertEqual(path.parent, root)
            handle.write('fixture log\n')
            handle.close()
            self.assertEqual(path.read_text(encoding='utf-8'), 'fixture log\n')
        finally:
            if not handle.closed:
                handle.close()

    def test_database_claim_adopts_existing_deterministic_file(self):
        root = Path.cwd() / ('existing-media-' + uuid.uuid4().hex)
        root.mkdir()
        output = root / 'output'; output.mkdir()
        path = output / 'existing.mp4'; path.write_bytes(b'old complete file')
        database = d.DownloadDatabase(root / 'clips4sale.db')
        clip = d.Clip.from_raw(record(503), LISTING)
        media = d.Media('https://cdn.example/existing.mp4', 'preview')
        try:
            database.upsert_clip(clip)
            self.assertFalse(database.claim_media(clip, media, path))
            saved = database.successful_media(clip, media)
            self.assertIsNotNone(saved)
            self.assertEqual(saved['path'], str(path))
        finally:
            database.close()

    def test_profile_lease_excludes_concurrent_profile_startup(self):
        root = Path.cwd() / ('profile-lease-' + uuid.uuid4().hex)
        profile = root / 'profile'; profile.mkdir(parents=True)
        first = d.acquire_profile_lease(profile)
        self.assertIsNotNone(first)
        try:
            self.assertIsNone(d.acquire_profile_lease(profile))
        finally:
            d.release_profile_lease(first)
        second = d.acquire_profile_lease(profile)
        self.assertIsNotNone(second)
        d.release_profile_lease(second)

    def test_goto_focuses_tab_and_rejects_about_blank(self):
        class Page:
            def __init__(self, remain_blank=False):
                self.url = 'about:blank'
                self.focused = 0
                self.remain_blank = remain_blank
            def bring_to_front(self):
                self.focused += 1
            def goto(self, url, **kwargs):
                if not self.remain_blank:
                    self.url = url
                return SimpleNamespace(status=200)
            def wait_for_timeout(self, _):
                pass

        page = Page()
        d.goto(page, LISTING, headless=True)
        self.assertEqual(page.url, LISTING)
        self.assertEqual(page.focused, 1)
        with self.assertRaises(d.DownloadError):
            d.goto(Page(remain_blank=True), LISTING, headless=True)

    def test_missing_media_http_errors_remain_retryable(self):
        error = RuntimeError('not found')
        error.response = SimpleNamespace(status_code=404)
        self.assertTrue(d.retryable_media_error(error))
        gone = RuntimeError('gone')
        gone.response = SimpleNamespace(status_code=410)
        self.assertTrue(d.retryable_media_error(gone))
        transient = RuntimeError('server error')
        transient.response = SimpleNamespace(status_code=503)
        self.assertTrue(d.retryable_media_error(transient))

    def test_browser_shutdown_suppresses_already_closed_driver_error(self):
        class Closed:
            def close(self):
                raise RuntimeError('Connection closed while reading from the driver')

        report = {'errors': []}
        d.close_browser_resources(Closed(), None, report)
        self.assertEqual(report['errors'], [])

    def test_headed_persistent_run_hands_profile_to_visible_browser(self):
        root = Path.cwd() / ('browser-handoff-' + uuid.uuid4().hex)
        profile = root / 'profile'
        profile.mkdir(parents=True)
        executable = root / 'chrome.exe'
        panel = SimpleNamespace(log=lambda message: None)
        args = SimpleNamespace(
            close_browser_on_exit=False, headless=False, no_persistent_login=False,
            _profile_actual=profile, browser='chrome', url=LISTING,
        )
        report = {'errors': []}
        with patch.object(d, 'browser_executable_for', return_value=executable), \
                patch.object(d.time, 'sleep') as sleep, \
                patch.object(d.subprocess, 'Popen') as popen:
            d.leave_browser_open(args, LISTING + '?resume=1', report, panel)
        sleep.assert_called_once_with(.5)
        command = popen.call_args.args[0]
        self.assertEqual(command[0], str(executable))
        self.assertIn(f'--user-data-dir={profile}', command)
        self.assertEqual(command[-1], LISTING + '?resume=1')
        self.assertTrue(report['browser_left_open']['left_open'])

    def test_close_browser_on_exit_disables_visible_browser_handoff(self):
        args = SimpleNamespace(
            close_browser_on_exit=True, headless=False, no_persistent_login=False,
            _profile_actual=Path.cwd(), browser='chrome', url=LISTING,
        )
        report = {'errors': []}
        with patch.object(d.subprocess, 'Popen') as popen:
            d.leave_browser_open(args, LISTING, report, SimpleNamespace(log=lambda message: None))
        popen.assert_not_called()
        self.assertFalse(report['browser_left_open']['left_open'])

    def test_download_pacer_uses_requested_video_pause_bands(self):
        panel = QuietPanel()
        pacer = d.DownloadPacer(panel)
        pacer.next_long_pause = 5
        for _ in range(5):
            pacer.video_downloaded()
        self.assertEqual(pacer.video_downloads, 5)
        self.assertEqual(len(panel.waits), 7)
        for seconds in panel.waits[:5]:
            self.assertGreaterEqual(seconds, d.VIDEO_PAUSE_RANGE[0])
            self.assertLessEqual(seconds, d.VIDEO_PAUSE_RANGE[1])
        self.assertGreaterEqual(panel.waits[5], d.FIVE_VIDEO_PAUSE_RANGE[0])
        self.assertLessEqual(panel.waits[5], d.FIVE_VIDEO_PAUSE_RANGE[1])
        self.assertGreaterEqual(panel.waits[6], d.LONG_VIDEO_PAUSE_RANGE[0])
        self.assertLessEqual(panel.waits[6], d.LONG_VIDEO_PAUSE_RANGE[1])
        self.assertTrue(all(round(seconds, 2) == seconds for seconds in panel.waits))

    def test_repeated_random_waits_stay_in_each_requested_range(self):
        for bounds in (d.VIDEO_PAUSE_RANGE, d.FIVE_VIDEO_PAUSE_RANGE,
                       d.LONG_VIDEO_PAUSE_RANGE, d.REUSED_VIDEO_PAUSE_RANGE):
            for repeated in bounds:
                with self.subTest(bounds=bounds, repeated=repeated):
                    panel = QuietPanel()
                    pacer = d.DownloadPacer(panel)
                    with patch.object(d.random, 'randrange', return_value=0):
                        for _ in range(20):
                            pacer.pause(repeated, bounds)
                    self.assertTrue(all(bounds[0] <= value <= bounds[1] for value in panel.waits))
                    self.assertTrue(all(a != b for a, b in zip(panel.waits, panel.waits[1:])))

    def test_fixed_waits_round_up_and_never_repeat_or_shorten(self):
        panel = QuietPanel()
        pacer = d.DownloadPacer(panel)
        with patch.object(d.random, 'randint', return_value=37):
            for _ in range(6):
                pacer.pause(2.001)
        self.assertEqual(panel.waits, [2.01, 2.38, 2.01, 2.38, 2.01, 2.38])
        self.assertEqual(pacer.pause(.001), .01)

    def test_zero_waits_do_not_sleep_or_erase_previous_wait(self):
        panel = QuietPanel()
        pacer = d.DownloadPacer(panel)
        pacer.pause(2.0)
        self.assertEqual(pacer.pause(0), 0)
        self.assertEqual(pacer.pause(0), 0)
        self.assertEqual(panel.waits, [2.0])
        with patch.object(d.random, 'randint', return_value=1):
            self.assertEqual(pacer.pause(2.0), 2.01)

    def test_browser_and_download_waits_share_history_and_actual_reporting(self):
        panel = QuietPanel()
        pacer = d.DownloadPacer(panel)
        browser_waits, scheduled = [], []
        page = SimpleNamespace(wait_for_timeout=browser_waits.append)
        with patch.object(d.random, 'randint', return_value=25):
            pacer.browser_pause(page, 2)
            pacer.pause(2, on_scheduled=scheduled.append)
            pacer.browser_pause(page, 2.25)
        self.assertEqual(browser_waits, [2000, 2500])
        self.assertEqual(panel.waits, [2.25])
        self.assertEqual(scheduled, panel.waits)

    def test_milestone_pauses_exclude_previous_other_kind_of_pause(self):
        panel = QuietPanel()
        pacer = d.DownloadPacer(panel)
        pacer.video_downloads = 4
        pacer.next_long_pause = 5
        # All three ranges overlap at 4.20. Even a fixed RNG must not repeat
        # that value back-to-back or get stuck trying to re-roll it.
        with patch.object(d, 'random_delay', return_value=4.2), \
                patch.object(d.random, 'randrange', return_value=0):
            pacer.video_downloaded()
        self.assertEqual(panel.waits, [4.2, 1.2, 4.2])

    def test_new_job_has_independent_wait_history(self):
        first, second = d.DownloadPacer(QuietPanel()), d.DownloadPacer(QuietPanel())
        self.assertEqual(first.pause(2), 2)
        self.assertEqual(second.pause(2), 2)
        self.assertNotEqual(first.pause(2), 2)

    def test_single_value_range_does_not_silently_break_bounds_or_repeat(self):
        pacer = d.DownloadPacer(QuietPanel())
        self.assertEqual(pacer.pause(2, (2, 2)), 2)
        with self.assertRaisesRegex(ValueError, 'no alternative'):
            pacer.pause(2, (2, 2))

    def test_hydration_is_parsed_without_execution(self):
        self.assertEqual(d.hydration_from_html('<script>window.__remixContext = {"x": 7}; alert(1)</script>'), {'x': 7})
        self.assertEqual(d.hydration_from_html('<script>window.__remixContext = evil()</script>'), {})


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path.cwd() / ('test-artifacts-' + uuid.uuid4().hex[:10])
        cls.root.mkdir()
        # Keep every synthetic test artifact; exercise the production warning
        # path instead of sending test fixtures to the user's Recycle Bin.
        recycle = patch('send2trash.send2trash', side_effect=OSError('Test retains staging files'))
        recycle.start()
        cls.addClassCleanup(recycle.stop)
        cls.ffmpeg, cls.ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
        if not cls.ffmpeg or not cls.ffprobe:
            raise unittest.SkipTest('FFmpeg/ffprobe required for media integration tests')
        cls.video = cls.root / 'synthetic.mp4'
        subprocess.run([cls.ffmpeg, '-hide_banner', '-loglevel', 'error', '-n', '-f', 'lavfi',
                        '-i', 'color=c=blue:s=160x90:r=10', '-t', '1.2', '-c:v', 'mpeg4',
                        str(cls.video)], check=True, capture_output=True)
        cls.media = cls.video.read_bytes()
        cls.requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                cls.requests.append(self.path)
                if self.path == '/missing-preview.mp4':
                    self.send_response(404); self.end_headers(); return
                if self.path == '/flaky.mp4' and cls.requests.count(self.path) == 1:
                    self.send_response(503); self.end_headers(); return
                if self.path == '/blocked.mp4':
                    self.send_response(429); self.end_headers(); return
                if self.path == '/stale.jpg':
                    self.send_response(404); self.end_headers(); return
                if self.path in ('/fallback.jpg', '/sidecar.gif'):
                    body, kind = ((b'GIF89a-fixture', 'image/gif') if self.path.endswith('.gif')
                                  else (b'fallback-jpeg', 'image/jpeg'))
                    self.send_response(200)
                    self.send_header('Content-Type', kind)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers(); self.wfile.write(body); return
                if self.path == '/not-video.mp4':
                    body, kind = b'<html>login required</html>', 'text/html'
                else:
                    body, kind = cls.media, 'video/mp4'
                self.send_response(200)
                self.send_header('Content-Type', kind)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'
        from playwright.sync_api import sync_playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'browser'): cls.browser.close()
        if hasattr(cls, 'playwright'): cls.playwright.stop()
        if hasattr(cls, 'server'):
            cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def new_context(self, route):
        context = self.browser.new_context(viewport={'width': 1000, 'height': 800})
        context.route('**/*', route)
        self.addCleanup(context.close)
        return context

    def test_headed_full_studio_discovery_starts_without_enter_gate(self):
        def route(request):
            request.fulfill(content_type='text/html', body=listing_html([record(801), record(802)]))
        context = self.new_context(route)
        url = 'https://www.clips4sale.com/studio/100/sample'
        args = d.parser().parse_args([url, '--scroll-delay', '.01', '--stable-rounds', '2'])
        self.assertFalse(args.pause_before_scrape)
        with patch('builtins.input', side_effect=AssertionError('Unexpected Enter gate')):
            clips, _, category = d.discover(context.new_page(), url, args, QuietPanel())
        self.assertEqual(len(clips), 2)
        self.assertEqual(category, 'All Categories')

    def test_video_category_tag_is_verified_and_media_packets_are_unchanged(self):
        tagged = d.tag_video_partial(self.video, '.mp4', 'Primary & Category', self.ffmpeg, self.ffprobe)
        self.assertNotEqual(tagged, self.video)
        self.assertEqual(self.video.read_bytes(), self.media)
        info = subprocess.run([self.ffprobe, '-v', 'error', '-show_entries', 'format_tags=genre',
                               '-of', 'json', str(tagged)], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(info.stdout)['format']['tags']['genre'], 'Primary & Category')
        def packet_hashes(path):
            result = subprocess.run([self.ffprobe, '-v', 'error', '-show_packets', '-show_data_hash', 'sha256',
                                     '-show_entries', 'packet=data_hash', '-of', 'json', str(path)],
                                    capture_output=True, text=True, check=True)
            return json.loads(result.stdout)['packets']
        self.assertEqual(packet_hashes(self.video), packet_hashes(tagged))

    def test_metadata_failure_preserves_raw_download_and_publishes_no_final_file(self):
        import requests
        output = self.root / 'tag-failure'; output.mkdir()
        with requests.Session() as session, \
                patch.object(d, 'tag_video_partial', side_effect=d.DownloadError('metadata test failure')):
            with self.assertRaisesRegex(d.DownloadError, 'metadata test failure'):
                d.download_media(session, d.Media(self.origin + '/preview.mp4', 'preview'), output,
                                 'sample', LISTING, QuietPanel(), video_category='Test',
                                 ffmpeg=self.ffmpeg, ffprobe=self.ffprobe)
        self.assertFalse((output / 'sample.mp4').exists())
        self.assertEqual((output / 'sample.mp4.part').read_bytes(), self.media)

    def test_scrolling_later_batch_quality_and_detail_extraction(self):
        initial = [record(i) for i in range(1, 25)]
        initial[0] = record(1, 'Same title (HD)', '720p')
        later = [record(i) for i in range(25, 49)]
        later[0] = record(25, 'Same title - 4K', '2160p')
        final = [record(49), record(50)]
        visited = []
        def route(request):
            url = request.request.url
            visited.append(url)
            if '/api/' in url:
                second = 'page=2' in url
                request.fulfill(json={'clips': later if second else final, 'has_more': second})
            else:
                request.fulfill(content_type='text/html', body=listing_html(initial, more=True))
        context = self.new_context(route)
        args = d.parser().parse_args([LISTING, '--headless', '--scroll-delay', '.06', '--stable-rounds', '5'])
        clips, studio, category = d.discover(context.new_page(), LISTING, args, QuietPanel())
        self.assertEqual(len(clips), 50)
        chosen, skipped = d.deduplicate(clips)
        self.assertEqual(len(chosen), 49)
        self.assertEqual(chosen[0].id, '25')
        self.assertEqual((studio, category), ('Sample Studio', 'Test'))
        self.assertEqual(sum('/api/' in u for u in visited), 2)

        all_url = LISTING.replace('/Cat5-test/', '/Cat0-AllCategories/')
        all_args = d.parser().parse_args([all_url, '--headless', '--scroll-delay', '.02', '--stable-rounds', '3'])
        all_clips, _, all_category = d.discover(context.new_page(), all_url, all_args, QuietPanel())
        self.assertEqual(len(all_clips), 50)
        self.assertEqual(all_category, 'All Categories')

    def test_incremental_newest_first_scan_stops_at_cached_boundary_and_merges_history(self):
        prior = [d.Clip.from_raw(record(i), LISTING) for i in range(1, 51)]
        initial = [record(i) for i in range(100, 124)]
        boundary = [record(124), *[record(i) for i in range(1, 24)]]
        visited = []

        def route(request):
            url = request.request.url
            visited.append(url)
            if '/api/' in url:
                request.fulfill(json={'clips': boundary, 'has_more': True})
            else:
                request.fulfill(content_type='text/html', body=listing_html(initial, more=True))

        context = self.new_context(route)
        url = LISTING.replace('/recommended/', '/C4SSort-display_order_desc/')
        args = d.parser().parse_args([url, '--headless', '--scroll-delay', '.03', '--stable-rounds', '4'])
        clips, studio, category = d.discover(
            context.new_page(), url, args, QuietPanel(), previous_clips=prior, previous_scroll_steps=10,
        )
        self.assertEqual((studio, category), ('Sample Studio', 'Test'))
        self.assertEqual(len(clips), 75)
        self.assertEqual({clip.id for clip in clips},
                         {str(i) for i in range(1, 51)} | {str(i) for i in range(100, 125)})
        self.assertEqual(args._last_discovery_new_clips, 25)
        self.assertIn('5 consecutive previously cached clips', args._last_discovery_stop_reason)
        self.assertLess(args._last_discovery_scroll_steps, 10)
        self.assertEqual(sum('/api/' in item for item in visited), 1)

    def test_streaming_duration_collision_and_block_handling(self):
        import requests
        output = self.root / 'streaming'; output.mkdir()
        existing = output / 'sample.mp4'; existing.write_bytes(b'keep me')
        with requests.Session() as session:
            path = d.download_media(session, d.Media(self.origin + '/preview.mp4', 'preview'),
                                    output, 'sample', LISTING, QuietPanel())
            self.assertEqual(path.name, 'sample (1).mp4')
            self.assertEqual(existing.read_bytes(), b'keep me')
            self.assertEqual(path.read_bytes(), self.media)
            self.assertAlmostEqual(d.probe_video(path, self.ffprobe)['duration'], 1.2, places=1)
            with self.assertRaises(d.DownloadError):
                d.download_media(session, d.Media(self.origin + '/not-video.mp4', 'preview'), output, 'bad', LISTING, QuietPanel())
            with self.assertRaises(d.SiteBlocked):
                d.download_media(session, d.Media(self.origin + '/blocked.mp4', 'preview'), output, 'blocked', LISTING, QuietPanel())
        self.assertEqual(len(list(output.iterdir())), 2)
        a = d.write_new_json(output / 'report.json', {'x': 1})
        b = d.write_new_json(output / 'report.json', {'x': 2})
        self.assertEqual(b.name, 'report (1).json')
        self.assertEqual(json.loads(a.read_text()), {'x': 1})

    def test_stale_best_image_falls_back_to_next_best_candidate(self):
        import requests
        output = self.root / 'image-fallback'; output.mkdir()
        media = d.Media(self.origin + '/stale.jpg', 'image', (self.origin + '/fallback.jpg',))
        with requests.Session() as session:
            path = d.download_media(session, media, output, 'best-image', LISTING, QuietPanel())
        self.assertEqual(path.name, 'best-image.jpg')
        self.assertEqual(path.read_bytes(), b'fallback-jpeg')

    def test_full_run_saves_preview_and_waits_measured_duration(self):
        records = [record(101), record(102)]
        def route(request):
            url = request.request.url
            match = d.CLIP_PATH.search(d.urlsplit(url).path)
            if match:
                raw = {**record(int(match[2])), 'customPreviewUrl': self.origin + '/preview.mp4'}
                body = page_html({'clip': raw, 'recommendations': [record(999)]})
            else:
                body = listing_html(records)
            request.fulfill(content_type='text/html', body=body)
        real_new_context = self.browser.new_context
        def new_context(**kwargs):
            context = real_new_context(**kwargs)
            context.route('**/*', route)
            self.addCleanup(context.close)
            return context
        browser = SimpleNamespace(new_context=new_context, close=lambda: None)
        @contextmanager
        def playwright_factory():
            yield SimpleNamespace(chromium=SimpleNamespace(launch=lambda **kwargs: browser))
        output = self.root / 'full-run'; output.mkdir()
        log_directory = self.root / 'logs'
        args = d.parser().parse_args([LISTING, '--headless', '--no-persistent-login', '--scroll-delay', '.02',
                                     '--stable-rounds', '3', '--page-delay', '.02'])
        panel = QuietPanel()
        with patch('playwright.sync_api.sync_playwright', playwright_factory), patch.object(d, 'ProgressPanel', return_value=panel), \
                patch.object(d, 'LOG_DIRECTORY', log_directory), \
                patch.object(d, 'private_database_path', return_value=output / d.DEFAULT_DATABASE_NAME), \
                patch.object(d, 'private_report_path', return_value=output / 'clips4sale-run.json'), \
                redirect_stdout(io.StringIO()):
            status = d.run(args, output, self.ffprobe)
        self.assertEqual(status, 0)
        self.assertEqual(len(list(output.glob('*.mp4'))), 1)
        self.assertEqual(len(panel.waits), 2)
        self.assertGreaterEqual(panel.waits[0], d.VIDEO_PAUSE_RANGE[0])
        self.assertLessEqual(panel.waits[0], d.VIDEO_PAUSE_RANGE[1])
        self.assertAlmostEqual(panel.waits[1], 1.2, places=1)
        report = json.loads((output / 'clips4sale-run.json').read_text())
        self.assertTrue(report['completed'])
        self.assertEqual(Path(report['logfile']).parent, log_directory)
        self.assertTrue(Path(report['logfile']).is_file())
        self.assertEqual(report['clips'][0]['filename_base'], 'Sample Studio - Test - Sample 101')
        self.assertEqual(report['clips'][0]['files'][0]['path'], report['clips'][1]['files'][0]['path'])

    def run_cached_fixture(self, output, records, panel=None):
        database = d.DownloadDatabase(output / d.DEFAULT_DATABASE_NAME)
        try:
            database.store_discovery(LISTING, [d.Clip.from_raw(raw, LISTING) for raw in records],
                                     'Sample Studio', 'Test')
        finally:
            database.close()
        visits = []

        def route(request):
            url = request.request.url
            visits.append(url)
            match = d.CLIP_PATH.search(d.urlsplit(url).path)
            raw = next(item for item in records if match and item['clipId'] == match[2])
            request.fulfill(content_type='text/html', body=page_html({'clip': raw}))

        def new_context(**kwargs):
            return self.new_context(route)

        browser = SimpleNamespace(new_context=new_context, close=lambda: None)

        @contextmanager
        def playwright_factory():
            yield SimpleNamespace(chromium=SimpleNamespace(launch=lambda **kwargs: browser))

        args = d.parser().parse_args([LISTING, '--headless', '--no-persistent-login', '--page-delay', '.01'])
        panel = panel or QuietPanel()
        with patch('playwright.sync_api.sync_playwright', playwright_factory), \
                patch.object(d, 'ProgressPanel', return_value=panel), \
                patch.object(d, 'LOG_DIRECTORY', output / 'logs'), \
                patch.object(d, 'private_database_path', return_value=output / d.DEFAULT_DATABASE_NAME), \
                patch.object(d, 'private_report_path', side_effect=lambda dry_run: output / (
                    'clips4sale-plan.json' if dry_run else 'clips4sale-run.json')), \
                patch.object(d, 'discover', side_effect=AssertionError('Cached listing must not be scraped')), \
                redirect_stdout(io.StringIO()):
            status = d.run(args, output, self.ffprobe)
        return status, visits, panel

    def test_404_retries_then_saves_other_assets_and_next_clip_and_resumes_without_duplicates(self):
        output = self.root / '404-queue'; output.mkdir()
        records = [
            {**record(901), 'customPreviewUrl': self.origin + '/missing-preview.mp4',
             'gifPreviewUrl': self.origin + '/sidecar.gif', 'cdn_previewlg_link': self.origin + '/fallback.jpg'},
            {**record(902), 'customPreviewUrl': self.origin + '/next-preview.mp4'},
        ]
        before = len(self.requests)
        status, visits, panel = self.run_cached_fixture(output, records)
        self.assertEqual(status, 1)
        requests = self.requests[before:]
        self.assertEqual(requests, ['/missing-preview.mp4', '/missing-preview.mp4',
                                    '/sidecar.gif', '/fallback.jpg', '/next-preview.mp4'])
        self.assertEqual(len(visits), 2)
        report = json.loads((output / 'clips4sale-run.json').read_text(encoding='utf-8'))
        self.assertTrue(report['completed'])
        self.assertEqual(report['errors'], [])
        self.assertEqual([item['http_status'] for item in report['clips'][0]['media_attempt_errors']], [404, 404])
        self.assertEqual(len(report['clips'][0]['files']), 2)
        self.assertEqual(len(report['clips'][1]['files']), 1)
        self.assertTrue(report['clips'][0]['errors'])
        self.assertFalse(report['clips'][1]['errors'])
        self.assertGreaterEqual(panel.waits[0], 1)
        self.assertLessEqual(panel.waits[0], 5)

        before = len(self.requests)
        status, visits, panel = self.run_cached_fixture(output, records)
        self.assertEqual(status, 1)
        self.assertEqual(self.requests[before:], ['/missing-preview.mp4', '/missing-preview.mp4'])
        self.assertEqual(len(visits), 1)
        report = json.loads((output / 'clips4sale-run (1).json').read_text(encoding='utf-8'))
        self.assertEqual([entry['clip_id'] for entry in report['clips']], ['902', '901'])
        self.assertEqual(report['clips'][0]['skipped'], 'already-complete')
        self.assertEqual(report['failed_queued_last'], 1)
        self.assertEqual(panel.waits, [])
        self.assertEqual(len(list(output.glob('*.mp4'))), 1)
        self.assertEqual(len(list(output.glob('*.gif'))), 1)
        self.assertEqual(len(list(output.glob('*.jpg'))), 1)

    def test_transient_http_failure_retries_same_claim_and_completes(self):
        output = self.root / 'recovered-retry'; output.mkdir()
        status, _, _ = self.run_cached_fixture(output, [
            {**record(903), 'customPreviewUrl': self.origin + '/flaky.mp4'},
        ])
        self.assertEqual(status, 0)
        report = json.loads((output / 'clips4sale-run.json').read_text(encoding='utf-8'))
        self.assertTrue(report['completed'])
        self.assertEqual(report['clips'][0]['errors'], [])
        self.assertEqual(len(report['clips'][0]['files']), 1)
        self.assertEqual(d.retry_ids_from_source(output / 'clips4sale-run.json')[0], set())
        database = d.DownloadDatabase(output / d.DEFAULT_DATABASE_NAME)
        try:
            row = database.connection.execute('SELECT status, attempts, owner_pid FROM media').fetchone()
            self.assertEqual(tuple(row), ('success', 2, None))
            self.assertEqual(database.failed_clip_ids(), set())
        finally:
            database.close()

    def test_interrupted_retry_log_keeps_failure_for_next_run(self):
        output = self.root / 'interrupted-retry'; output.mkdir()

        class InterruptedPanel(QuietPanel):
            def log(self, text):
                if '🔁 Retry' in text:
                    raise KeyboardInterrupt()

        records = [{**record(904), 'customPreviewUrl': self.origin + '/missing-preview.mp4'}]
        with self.assertRaises(KeyboardInterrupt):
            self.run_cached_fixture(output, records, InterruptedPanel())
        self.assertEqual(d.retry_ids_from_source(output / 'clips4sale-run.json')[0], {('100', '904')})
        database = d.DownloadDatabase(output / d.DEFAULT_DATABASE_NAME)
        try:
            self.assertIn(('100', '904'), database.failed_clip_ids())
            row = database.connection.execute('SELECT status, error FROM media').fetchone()
            self.assertEqual(row['status'], 'processing')
            self.assertIn('404', row['error'])
        finally:
            database.close()


if __name__ == '__main__':
    unittest.main()
