"""V447 behavior: curation, learned selectors, layout relationships and experiments."""
import math
import contextlib
import io
import json
import re
import subprocess
from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as p


class CurationTests(unittest.TestCase):
    def test_rejected_words_stay_text_in_actual_lookup(self):
        for word in ('true', 'false', "aren't", 'aren’t', 'swear', 'good', 'bad',
                     'starting', 'ending', 'welcome', 'murphy', "murphy's",
                     'murphy’s', 'spelling', 'drinking', 'throwing'):
            with self.subTest(word=word):
                self.assertIsNone(p.emojimax_replacement_for_key(word))
                self.assertNotIn(word, p.SEMANTIC_PHRASES)
        self.assertNotEqual(p.emojimax_replacement_for_key('ladies'),
                            p.emojimax_replacement_for_key('men'))
        self.assertIsNotNone(p.emojimax_replacement_for_key('broken'))


class LearnedSelectorTests(unittest.TestCase):
    def test_normalized_selector_and_real_neighbor_collisions(self):
        # No filesystem writes: use the real matching logic on a mocked directory.
        target = Path(r'C:\music\Mom - Goddess (live) (youtube-rip).flac')
        siblings = [target]
        with mock.patch.object(Path, 'iterdir', return_value=iter(siblings)), \
             mock.patch.object(Path, 'is_file', return_value=True):
            selector = p._attrib_rule_selector_for_audio(target)
        self.assertEqual(r'^Mom.*Goddess.*live.*youtube\-rip', selector)
        self.assertTrue(p._attrib_selector_matches_audio(selector, target, target.parent))
        # A wildcard must not quietly tag both a live and a differently named file.
        other = target.with_name('Mom Goddess lively youtube-rip.flac')
        with mock.patch.object(Path, 'iterdir', side_effect=lambda: iter([target, other])), \
             mock.patch.object(Path, 'is_file', return_value=True):
            selector = p._attrib_rule_selector_for_audio(target)
        self.assertTrue(p._attrib_selector_matches_audio(selector, target, target.parent))
        self.assertFalse(p._attrib_selector_matches_audio(selector, other, target.parent))

    def test_apostrophes_and_regex_metacharacters(self):
        selector = p.normalized_learned_title_selector("O’Connor's (live) [a+b]")
        self.assertEqual(r'^O.*Connor.*s.*live.*\[a\+b\]', selector)
        self.assertNotIn(' ', selector)


class HudAnchorTests(unittest.TestCase):
    def test_shared_play_value_anchor_and_balanced_intermediate_fields(self):
        for width, title in ((140, 'Sunkissed'), (165, 'Sunkissed'), (190, 'Wide 界 title')):
            tags = {'Artist': 'Rain on Fridays', 'Song': title, 'Year': '2023',
                    'URL': 'https://RainOnFridays.bandcamp.com'}
            header = '▶ Play: ' + ('a' * 45) + '\\' + title + '.flac (3:00)'
            rows, ansi = p.format_tag_panel(tags, width=width, play_header_text=header)
            row = next(row for row in rows if 'Song:' in row)
            positions = {label: colon - len(label) for label, colon in p.hud_metadata_label_colons([row])}
            song_start = positions['Song'] + len('Song: ')
            self.assertEqual(p.terminal_cell_width(header[:header.index(title)]), song_start)
            self.assertIn('Song: ' + title, row)  # Move the entire field, not its colon padding.
            song_end = song_start + p.terminal_cell_width(title)
            year_end = positions['Year'] + len('Year: 2023')
            self.assertLessEqual(abs((positions['Year'] - song_end) - (positions['URL'] - year_end)), 1)
            self.assertEqual(1, len(rows))
            self.assertTrue(all(p.terminal_cell_width(row) <= width for row in rows))

    def test_unavailable_or_impossible_anchor_keeps_all_fields(self):
        tags = {'Artist': 'Example band', 'Song': 'A long song title', 'Album': 'Album',
                'Year': '2023', 'Genre': 'Rock', 'Composer': 'Composer', 'Comment': 'Comment'}
        for width in (65, 90, 140, 200):
            ordinary = p.format_tag_panel(tags, width=width)
            missing = p.format_tag_panel(tags, width=width, play_header_text='▶ Play: other.flac')
            impossible = p.format_tag_panel(tags, width=width,
                                            play_header_text='▶ Play: ' + 'x' * 300 + tags['Song'])
            self.assertEqual(ordinary, missing)
            self.assertEqual(ordinary, impossible)


class AdaptiveFrequencyTests(unittest.TestCase):
    def test_opt_in_delay_smooth_contraction_expansion_and_reset(self):
        bins = bytes([32] * 25 + [0] * 75)
        allocator = p.AdaptiveFrequencyAllocator()
        for tick in range(30):
            self.assertEqual(1.0, allocator.update(bins, tick * .2))
        values = [allocator.update(bins, tick * .2, enabled=True) for tick in range(31)]
        self.assertEqual([1.] * 10, values[:10])
        self.assertTrue(all(a >= b for a, b in zip(values, values[1:])))
        self.assertAlmostEqual(.33, values[-1])
        self.assertEqual(1., allocator.update(bytes([32] * 100), 6.2, enabled=True))
        self.assertEqual(1., allocator.update(bins, 1., enabled=True))  # Seek.
        self.assertEqual(1., allocator.update(bins, 1.2, enabled=True, source_key='mic'))
        self.assertEqual(0, p.PLAYER_SETTING_DEFAULTS['AdaptiveFrequency'])

    def test_silence_no_op_and_browser_equivalence(self):
        bins = bytes(range(64))
        self.assertIs(bins, p.resample_adaptive_spectrum(bins, 1))
        self.assertEqual(bytes(64), p.resample_adaptive_spectrum(bytes(64), .3))
        html = p._paf_web_html()
        function = html[html.index('function adaptiveFrequencyBins('):html.index('function browserSpectrumProcess(')]
        script = 'const latestState={adaptive_frequency_enabled:true,adaptive_frequency_fraction:.37};\n'
        script += function + '\nconsole.log(JSON.stringify(Array.from(adaptiveFrequencyBins(Uint8Array.from(' + json.dumps(list(bins)) + ')))));'
        result = subprocess.run([p.shutil.which('node'), '-e', script], capture_output=True, text=True, check=True)
        self.assertEqual(list(p.resample_adaptive_spectrum(bins, .37)), json.loads(result.stdout))


class LoudnessTests(unittest.TestCase):
    def snapshot(self, name='vlc', pid=20, other=()):
        return {'known': True, 'active': ('VLC',), 'excluded_families': (), 'default_endpoint': 'A',
                'endpoints': [{'id': 'A', 'name': 'Speakers', 'master_db': -6., 'muted': False}],
                'audio': [{'name': name, 'processId': pid, 'state': 1, 'peak': .1, 'endpoint_id': 'A'}] + list(other)}

    def test_gate_minimum_and_bounded_storage(self):
        window = p.GatedLoudnessWindow()
        for _ in range(12): window.add(.01)
        self.assertIsNone(window.estimate())
        window.add(.01)
        for _ in range(30): window.add(0)
        self.assertAlmostEqual(.01, window.estimate())
        for _ in range(30): window.add(.000001)
        self.assertAlmostEqual(.01, window.estimate())  # Relative silence excluded.
        for _ in range(1000): window.add(.01)
        self.assertEqual(150, len(window.blocks))

    def test_raise_reduce_master_compensation_and_existing_limits(self):
        # Reference already contains ReplayGain, Windows session gain and mixing.
        ref = .01
        self.assertEqual(178, p.loudness_match_volume(ref, .04, 0, 100))
        self.assertEqual(45, p.loudness_match_volume(ref, .0025, 0, 100))
        for master in (-30, -12, -6, 0):
            self.assertEqual(100, p.loudness_match_volume(ref, ref * 10**(master/10), master, 100))
        self.assertEqual(45, p.loudness_match_volume(ref, ref * 10**(-12/10), -6, 100))
        self.assertEqual(398, p.loudness_match_volume(ref, 1, 0, 100))
        self.assertIsNone(p.loudness_match_volume(ref, .01, 0, 0))
        self.assertIsNone(p.loudness_match_volume(None, .01, 0, 100))

    def test_k_weighting_level_scale_chunk_continuity_and_lfe(self):
        import numpy as np
        rate = 48000
        tone = .1 * np.sin(2 * np.pi * 1000 * np.arange(38400) / rate)
        stereo = np.column_stack((tone, tone)).astype('<f4')
        meter = p.KWeightedBlockMeter(rate, 2)
        first = meter.power(stereo[:19200].tobytes())
        second = meter.power(stereo[19200:].tobytes())
        self.assertAlmostEqual((first + second) / 2,
                               p.KWeightedBlockMeter(rate, 2).power(stereo.tobytes()), places=10)
        self.assertAlmostEqual(-20, -.691 + 10 * math.log10(second), delta=.15)
        half = p.KWeightedBlockMeter(rate, 2).power((stereo * .5).tobytes())
        whole = p.KWeightedBlockMeter(rate, 2).power(stereo.tobytes())
        self.assertAlmostEqual(whole / 4, half, places=10)
        surround = np.zeros((len(tone), 6), dtype='<f4'); surround[:, 3] = tone
        self.assertEqual(0, p.KWeightedBlockMeter(rate, 6).power(surround.tobytes()))

    def test_rejects_notifications_nest_wrong_outputs_and_manual_pause(self):
        context = {'pids': (10,), 'paused': True, 'automatic': True, 'volume': 100}
        self.assertEqual('external', p.loudness_sample_source(self.snapshot(), 'A', context)[0])
        notification = {'name': 'system sounds', 'processId': 0, 'state': 1, 'peak': 0., 'endpoint_id': 'A'}
        self.assertIsNone(p.loudness_sample_source(self.snapshot(other=[notification]), 'A', context)[0])
        nest = self.snapshot('chrome'); nest.update(active=('chrome',), excluded_families=('chrome',))
        self.assertIsNone(p.loudness_sample_source(nest, 'A', context)[0])
        second = {'name': 'vlc', 'processId': 21, 'state': 1, 'peak': .1, 'endpoint_id': 'B'}
        self.assertIsNone(p.loudness_sample_source(self.snapshot(other=[second]), 'A', context)[0])
        self.assertIsNone(p.loudness_sample_source(self.snapshot(), 'A', {**context, 'automatic': False})[0])
        music = {**context, 'paused': False}
        self.assertEqual('music', p.loudness_sample_source(self.snapshot('python', 10), 'A', music)[0])
        self.assertIsNone(p.loudness_sample_source(self.snapshot('python', 10), 'A', {**music, 'fade': True})[0])

    def test_episode_result_manual_override_and_output_change(self):
        matcher = p.PAFExternalLoudnessMatcher(None)
        matcher.configure('track', 100, (10,), 'System default')
        matcher.endpoint_id = 'A'
        matcher.set_pause(True, True)
        for _ in range(15):
            matcher.reference.add(.01)
            matcher.external.add(.04 * 10**(-6/10))
        self.assertEqual(178, matcher.result(100, self.snapshot(), 'track')[0])
        self.assertIsNone(matcher.result(80, self.snapshot(), 'track')[0])
        self.assertIsNone(matcher.result(100, self.snapshot(), 'new track')[0])
        changed = self.snapshot(); changed['default_endpoint'] = 'B'
        self.assertEqual(50, matcher.result(100, changed, 'track')[0])  # Unverified output uses the approved safety duck.
        matcher.set_pause(True, False)
        self.assertIsNone(matcher.result(100, self.snapshot(), 'track')[0])

    def test_real_player_applies_visible_volume_only_on_automatic_resume(self):
        class Process:
            def __init__(self): self.running = True
            def poll(self): return None if self.running else 0
            def terminate(self): self.running = False
            kill = terminate
            def wait(self, timeout=None): self.running = False; return 0
        class Monitor:
            def snapshot(self, now=None): return {'known': True, 'active': self.active}
            def close(self): pass
            active = ()
        monitor = Monitor()
        coordinator = p.PAFExternalPlaybackCoordinator(monitor)
        coordinator.filter_action(None, False, 0)
        monitor.active = ('VLC',)
        clock, calls, volume = [100.], [0], [100]
        def action():
            clock[0] += 1
            calls[0] += 1
            if calls[0] >= 2: monitor.active = ()
            return p.STOP if calls[0] > 6 else None
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            for name in ('update_lastfm_now_playing_async', 'append_pafplayer_trace', 'record_local_play_history',
                         'write_now_playing_files', 'start_background_audio_health_check', 'set_console_title',
                         'scrobble_track_async', 'playlist_history_mark_played', 'save_spectrum_timeline_cache'):
                if hasattr(p, name): stack.enter_context(mock.patch.object(p, name))
            save = stack.enter_context(mock.patch.object(p, 'save_player_setting_value'))
            stack.enter_context(mock.patch.object(coordinator.loudness, 'result', return_value=(160, 'Loudness matched: 100% → 160%')))
            stack.enter_context(mock.patch.object(p, 'LASTFM_SCROBBLING', False, create=True))
            p.play_audio_file(Path(__file__).with_name('pafplayer_v416_timing_fixture.wav'),
                ffplay=Path('ffplay.exe'), duration_probe=lambda _: 60,
                key_action_reader=action, process_factory=lambda *a, **k: Process(),
                monotonic=lambda: clock[0], sleeper=lambda _: None,
                install_signal_handlers=False, drcs_visualizer=False, sixel_visualizer=False,
                lyrics_display=False, looping=False, now_playing_targets=[], volume_state=volume,
                manage_winamp=False, external_media_controller=coordinator, visualizer_input_source_state=[0],
                attribute_management_enabled=False, theory_modes={13, 36})
            self.assertEqual([160], volume)
            save.assert_any_call('Volume', 160)


class WebConfigurationTests(unittest.TestCase):
    def test_javascript_syntax_and_setting_routes(self):
        html = p._paf_web_html()
        script = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.S))
        result = subprocess.run([p.shutil.which('node'), '--check', '-'], input=script,
                                text=True, encoding='utf-8', capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("['adaptive_frequency_enabled','AdaptiveFrequency']", script)
        self.assertIn("['external_media_loudness_match','ExternalMediaLoudnessMatch']", script)
        self.assertIn('adaptiveFrequencyBins(scheduled)', script)
        self.assertNotIn("['adaptive_frequency_enabled','AdaptiveFrequency',null]", script)


if __name__ == '__main__':
    unittest.main()
