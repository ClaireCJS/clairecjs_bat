"""V629 official-instance randomization and resume alias regressions."""
import contextlib
import io
from pathlib import Path
import types
import unittest
import uuid
from unittest import mock

import PAFPlayer as player
from PAFPlayer_instance import Instance
from PAFPlayer_workflows import recycle


class RandomizeTests(unittest.TestCase):
    def test_random_order_keeps_current_slot_and_duplicate_members(self):
        a, b, c = (Path(name) for name in ('a.mp3', 'b.mp3', 'c.mp3'))
        order = [a, b, b, c]
        result = player.randomized_playlist_order(order, b, shuffle=list.reverse)
        self.assertEqual([b, c, b, a], result)
        self.assertEqual([a, b, b, c], order)

    def test_no_official_instance_is_an_error_and_creates_no_player(self):
        class MissingInstance:
            def __init__(self, runtime): pass
            def acquire(self): return True
            def close(self): pass
            def forward(self, request): raise AssertionError('must not forward')
        error = io.StringIO()
        with mock.patch.object(player, 'paf_workflows', return_value=object()), \
             mock.patch('PAFPlayer_instance.Instance', MissingInstance), \
             contextlib.redirect_stderr(error):
            self.assertEqual(2, player.main(['randomize']))
        self.assertIn('no pafplayer instance to randomize', error.getvalue())

    def test_both_standalone_spellings_forward_only_to_owner(self):
        requests = []
        class RunningInstance:
            def __init__(self, runtime): pass
            def acquire(self): return False
            def close(self): pass
            def forward(self, request):
                requests.append(request)
                return {'ok': True, 'message': 'Playlist randomized in the official player'}
        with mock.patch.object(player, 'paf_workflows', return_value=object()), \
             mock.patch('PAFPlayer_instance.Instance', RunningInstance), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, player.main(['randomize']))
            self.assertEqual(0, player.main(['--randomize']))
        self.assertEqual([{'randomize': True}, {'randomize': True}], requests)

    def test_single_file_warning_is_not_an_error(self):
        class RunningInstance:
            def __init__(self, runtime): pass
            def acquire(self): return False
            def close(self): pass
            def forward(self, request):
                return {'ok': True, 'warning': True, 'message': 'single-file mode; no playlist to randomize'}
        output = io.StringIO()
        with mock.patch.object(player, 'paf_workflows', return_value=object()), \
             mock.patch('PAFPlayer_instance.Instance', RunningInstance), \
             contextlib.redirect_stdout(output):
            self.assertEqual(0, player.main(['--randomize']))
        self.assertIn('warning:', output.getvalue())

    def test_resume_alias_uses_same_missing_checkpoint_result(self):
        outputs = []
        with mock.patch.object(player, 'load_last_resumable_playlist', return_value=None):
            for spelling in ('resume', '--resume'):
                error = io.StringIO()
                with contextlib.redirect_stderr(error):
                    self.assertEqual(2, player.main([spelling]))
                outputs.append(error.getvalue())
        self.assertEqual(outputs[0], outputs[1])

    def test_positional_playlist_randomize_is_forwarded_to_official_instance(self):
        requests = []
        playlist = Path('a_playlist.m3u').absolute()
        class RunningInstance:
            def __init__(self, runtime): pass
            def acquire(self): return False
            def close(self): pass
            def forward(self, request):
                requests.append(request)
                return {'ok': True, 'queued': 2, 'message': 'Loaded and randomized playlist'}
        with mock.patch.object(player, 'paf_workflows', return_value=types.SimpleNamespace(close=lambda: None)), \
             mock.patch.object(player, 'paf_inprocess_test_isolation_active', return_value=False), \
             mock.patch.object(player, 'ensure_standard_music_collection_aliases', return_value=True), \
             mock.patch.object(player, 'load_mp3_base_attribute_rules'), \
             mock.patch.object(player, 'load_player_settings', return_value=dict(player.PLAYER_SETTING_DEFAULTS)), \
             mock.patch.object(player, 'ensure_clairecjs_dependency'), \
             mock.patch.object(player, 'start_pafplayer_diagnostic_session'), \
             mock.patch('PAFPlayer_cli_workflows.dispatch', side_effect=lambda _runtime, args: (None, args)), \
             mock.patch('PAFPlayer_monkeymote.parse_options', side_effect=lambda args: (args, {})), \
             mock.patch('PAFPlayer_instance.Instance', RunningInstance), \
             mock.patch('PAFPlayer_instance.resolve_request', return_value={
                 'paths': ['first.mp3', 'second.mp3'], 'playlist': str(playlist)}), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, player.main([str(playlist), '--randomize']))
        self.assertEqual([{'paths': ['first.mp3', 'second.mp3'],
                           'playlist': str(playlist), 'randomize': True}], requests)

    def test_ipc_randomize_requires_true_and_calls_owner_bridge(self):
        root = Path(__file__).parent / 'runs' / ('v629-randomize-' + uuid.uuid4().hex)
        root.mkdir(parents=True)
        self.addCleanup(lambda: recycle(root))
        calls = []
        runtime = types.SimpleNamespace(root=root, randomize_bridge=lambda: calls.append('owner') or
                                        {'message': 'Playlist randomized in the official player'})
        instance = Instance(runtime)
        instance.start()
        self.addCleanup(instance.close)
        self.assertEqual('Playlist randomized in the official player',
                         instance.forward({'randomize': True})['message'])
        self.assertEqual(['owner'], calls)
        with self.assertRaisesRegex(ValueError, 'Invalid randomize request'):
            instance.forward({'randomize': False})

    def test_ipc_playlist_load_randomizes_only_after_load(self):
        root = Path(__file__).parent / 'runs' / ('v629-randomize-load-' + uuid.uuid4().hex)
        root.mkdir(parents=True)
        self.addCleanup(lambda: recycle(root))
        song = root / 'song.mp3'
        song.write_bytes(b'one')
        playlist = root / 'list.m3u'
        playlist.write_text(str(song), encoding='utf-8')
        sequence = []
        runtime = types.SimpleNamespace(
            root=root,
            app=types.SimpleNamespace(AUDIO_EXTENSIONS={'.mp3'}),
            queue_bridge=lambda *_: None,
            randomize_bridge=lambda: sequence.append('randomize') or {'message': 'randomized'},
        )
        instance = Instance(runtime)
        instance.start()
        self.addCleanup(instance.close)
        with mock.patch('PAFPlayer_web_workflows.queue_snapshot', return_value={'entries': [], 'revision': 0}), \
             mock.patch('PAFPlayer_web_workflows.edit_queue', side_effect=lambda *_args, **_kwargs: sequence.append('load') or {'revision': 1}):
            result = instance.forward({'paths': [str(song)], 'playlist': str(playlist), 'randomize': True})
            self.assertEqual('Loaded and randomized playlist', result['message'])
            self.assertEqual(['load', 'randomize'], sequence)
            with self.assertRaisesRegex(ValueError, 'requires one playlist'):
                instance.forward({'paths': [str(song)], 'randomize': True})
            self.assertEqual(['load', 'randomize'], sequence)


if __name__ == '__main__':
    unittest.main()
