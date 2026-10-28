"""Behavioral regressions for timestamped playback, TODOs and Windows Terminal spacing."""
import base64
import ctypes
import inspect
import json
import unittest
from unittest import mock

import play_audio_file as p


class KaraokeAndCurationTests(unittest.TestCase):
    def test_sung_wrapper_preserves_exact_generated_spacing_for_every_digit(self):
        for number in range(1, 11):
            for style in (1, 2, 5):
                neighbor = p.stylize_karaoke_with_emojimax(
                    f'{number} qzx', style, True, force_emoji_when_enabled=True,
                    windows_terminal_compat=True)
                sung = p.wrap_to_cells(neighbor, 80)
                self.assertEqual([neighbor], sung)
                self.assertIn('   ', sung[0])
                for treatment in range(1, len(p.KARAOKE_TREATMENT_NAMES) + 1):
                    painted = p.colorize_karaoke_text(sung[0], treatment, 0, 1.0)
                    self.assertEqual(sung[0], p.ANSI_CSI_RE.sub('', painted))

    def test_wrapping_counts_safety_cells_and_keeps_literal_glyphs_untouched(self):
        self.assertEqual(['❷   qzx'], p.wrap_to_cells('❷   qzx', 7))
        self.assertEqual(['❷', 'qzx'], p.wrap_to_cells('❷   qzx', 6))
        self.assertEqual(['❷ qzx'], p.wrap_to_cells('❷ qzx', 7))
        for wt in (False, True):
            literal = p.stylize_karaoke_with_emojimax('❷ qzx ⬆️', 1, True, windows_terminal_compat=wt)
            self.assertEqual('❷ qzx ⬆️', literal)
        self.assertEqual([''], p.wrap_to_cells('', 20))

    def test_up_is_generated_only_and_play_has_no_extra_space(self):
        for key, glyph in [('up', '⬆️'), ('play', '▶️')]:
            plain = p.stylize_karaoke_with_emojimax(f'{key} qzx', 1, True)
            wt = p.stylize_karaoke_with_emojimax(f'{key} qzx', 1, True, windows_terminal_compat=True)
            self.assertEqual(plain.replace(' qzx', '  qzx') if key == 'up' else plain, wt)

    def test_final_semantics_and_inflections(self):
        for word in p.EMOJIMAX_V416_REMOVED:
            self.assertIsNone(p.emojimax_replacement_for_key(word), word)
            self.assertNotIn(word, p.SEMANTIC_PHRASES)
        for key, value in {'grew': '🌱', 'person': '👤', '30': '㉚', 'thirty': '㉚', 'broken': '💔'}.items():
            self.assertEqual(value, p.emojimax_plain_with_solutions(key)[0])
        for key, (base, suffix) in p.EMOJIMAX_BASE_SUFFIX.items():
            self.assertEqual(p.emojimax_replacement_for_key(base) + suffix, p.emojimax_replacement_for_key(key))
        self.assertIsNotNone(p.emojimax_replacement_for_key('wish'))
        self.assertIsNotNone(p.emojimax_replacement_for_key('pray'))

    def test_j_and_url_display(self):
        for key in ('j', 'J'):
            self.assertEqual(p.PLAYLIST_ADD_SEARCH, p.interpret_console_key(key))
        self.assertEqual('example.com/a', p.compact_url_display_text('https://www.example.com/a/'))
        link = p.osc8_hyperlink('https://example.com/', p.compact_url_display_text('https://example.com/'))
        self.assertIn('https://example.com/', link)
        self.assertIn('example.com' + p.OSC8_CLOSE, link)


class ClockAndPulseTests(unittest.TestCase):
    def test_device_timestamp_not_arrival_time_or_decoder_start_is_the_clock(self):
        process = mock.Mock(playback_clock={'seconds': 4.0, 'at': 100.0, 'queued_seconds': .5})
        self.assertAlmostEqual(8.1, p.audio_segment_elapsed(process, 100.05, 80, 2.0))
        self.assertAlmostEqual(4.15, p.audio_segment_elapsed(process, 109, 80, 1.0))
        process.playback_clock['queued_seconds'] = .01
        self.assertAlmostEqual(4.01, p.audio_segment_elapsed(process, 100.1, 80, 1.0))
        self.assertEqual(0, p.audio_segment_elapsed(object(), 10, 0, 1, waiting=True))
        self.assertEqual(6, p.audio_segment_elapsed(object(), 10, 7, 2))

    def test_winmm_returns_samples_ms_or_bytes(self):
        process = object.__new__(p.MatrixMixerInspiredWaveOutProcess)
        process._playback_started_at = 1
        process._wave_handle = ctypes.c_void_p(1)
        process.sample_rate = 48000
        process.channels = 8
        process.container_bits = 32
        process.initial_delay_ms = 25
        process._pending_headers = ()
        for kind, value in ((2, 48000), (1, 1000), (4, 48000 * 8 * 4)):
            def position(_handle, stamp, _size):
                stamp._obj.wType = kind
                stamp._obj.u.value = value
                return 0
            process._winmm = mock.Mock(waveOutGetPosition=position)
            self.assertAlmostEqual(.975, process.playback_clock['seconds'])
        self.assertEqual(12, ctypes.sizeof(p._MMTime))

    def test_silence_clears_all_detectors_without_a_falling_edge_beat(self):
        for detector in range(1, 6):
            state = {}
            p.progress_beat_pulse([50] * 12, state, .03, detector)
            self.assertEqual(0, p.progress_beat_pulse([0] * 12, state, .03, detector))
            self.assertEqual(0, p.progress_beat_pulse([], state, .03, detector))
            self.assertEqual({'pulse': 0.0}, state)

    def test_prescheduled_pulses_do_not_depend_on_fps_seeks_or_paint_stalls(self):
        width, fps = 12, 30
        frames = [bytes([0] * width) for _ in range(90)]
        for start in (15, 45):
            for frame in range(start, start + 3):
                frames[frame] = bytes([60] * width)
        timeline = p.ProgressBeatTimeline()
        timeline.append(b''.join(frames[:40]), width, fps)
        timeline.append(b''.join(frames[40:]), width, fps)
        for detector in range(1, 6):
            first = timeline.at(.5, detector)
            self.assertGreater(first, 0, detector)
            for timestamp in (2, 1.0, 2.8, .1, 1.5, 1.6):
                timeline.at(timestamp, detector)
            self.assertEqual(first, timeline.at(.5, detector))
            self.assertEqual(0, timeline.at(1.61, detector))
            self.assertEqual(0, timeline.at(3.0, detector))

    def test_global_seek_capture_retains_rapid_presses_during_restart(self):
        capture = p.GlobalSeekCapture()
        for direction, when in [(1, 0), (0, .03), (1, .06), (0, .09), (1, .12), (1, .46)]:
            capture.sample(direction, when)
        self.assertEqual(25, capture.drain())
        self.assertEqual(0, capture.drain())
        capture.sample(-1, .50)
        self.assertEqual(-5, capture.drain())
        self.assertEqual(25, p.seek_seconds_for_action(p.GLOBAL_SEEK_PREFIX + '25'))


class BufferedWebAndArtworkTests(unittest.TestCase):
    def server(self):
        cls = next(value for value in vars(p).values() if isinstance(value, type) and hasattr(value, 'timeline_snapshot'))
        server = object.__new__(cls)
        server._timeline_sample = None
        return server

    def test_web_window_includes_future_frames_with_clock_anchor(self):
        server = self.server()
        data = bytes(range(240)) * 12
        server.publish_timeline((data, 12, 30), 2, 2, 100, ui_start=1)
        with mock.patch.object(p.time, 'monotonic', return_value=100.05):
            payload = server.timeline_snapshot()
        self.assertAlmostEqual(2.1, payload['position'])
        self.assertEqual(1, payload['ui_start'])
        self.assertTrue(payload['playing'])
        start = payload['start_frame'] * 12
        raw = base64.b64decode(payload['frames'])
        self.assertEqual(data[start:start + len(raw)], raw)
        self.assertGreater(len(raw) / 12 / 30, 3)
        with mock.patch.object(p.time, 'monotonic', return_value=110):
            self.assertFalse(server.timeline_snapshot()['playing'])

    def test_web_paused_live_and_stopped_do_not_replay_track_frames(self):
        server = self.server()
        self.assertEqual('stopped', server.timeline_snapshot()['source'])
        server.publish_timeline((bytes(120), 12, 30), 1, 0, 100, playing=False, live=True)
        with mock.patch.object(p.time, 'monotonic', return_value=100):
            payload = server.timeline_snapshot()
        self.assertEqual('live', payload['source'])
        self.assertEqual('', payload['frames'])

    def test_artwork_choices_and_real_gap_cleanup(self):
        schema = p.paf_web_control_schema()
        choice = next(item for item in schema['selects'] if item['key'] == 'artwork_seam_strategy')
        self.assertEqual(list(range(6)), [item['value'] for item in choice['options']])
        self.assertEqual(0, p.PLAYER_SETTING_DEFAULTS['ArtworkSeamStrategy'])
        for value in range(6):
            self.assertTrue(p.paf_web_action_is_allowed(f'web-set:artwork_seam_strategy:{value}'))
        self.assertFalse(p.paf_web_action_is_allowed('web-set:artwork_seam_strategy:6'))
        bright = ((100, 100, 100), (80, 80, 80), '█')
        black = ((0, 0, 0), (0, 0, 0), ' ')
        self.assertEqual((100, 100, 100), p.fill_artwork_vertical_gaps(((bright, black, bright),))[0][1][1])
        self.assertEqual(((black, black, bright),), p.fill_artwork_vertical_gaps(((black, black, bright),)))


if __name__ == '__main__':
    unittest.main()
