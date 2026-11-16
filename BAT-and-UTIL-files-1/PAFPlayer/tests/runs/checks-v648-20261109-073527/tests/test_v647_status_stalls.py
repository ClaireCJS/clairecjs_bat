"""The actual periodic publisher must not reload settings or report stale titles."""
import ast
import inspect
import unittest
from unittest import mock
import PAFPlayer as app


class PeriodicStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        play=ast.parse(inspect.getsource(app.play_audio_file)).body[0]
        publish=next(n for n in ast.walk(play) if isinstance(n,ast.Call) and
                     isinstance(n.func,ast.Attribute) and n.func.attr=='publish' and len(n.keywords)>100)
        cls.publish=publish
        fields=[k for k in publish.keywords if k.arg and k.arg.startswith('console_title_')]
        cls.expression=compile(ast.fix_missing_locations(ast.Expression(ast.Dict(
            keys=[ast.Constant(k.arg) for k in fields],values=[k.value for k in fields]))),
            '<production periodic title fields>','eval')

    def test_live_titles_do_not_read_registry(self):
        loader=mock.Mock(side_effect=AssertionError('Bulk settings read blocks visualizer'))
        ns=dict(load_player_settings=loader,console_title_style=19,console_title_content=2,
                CONSOLE_TITLE_SWEEPS=app.CONSOLE_TITLE_SWEEPS)
        result=eval(self.expression,ns)
        self.assertEqual(19,result['console_title_style'])
        self.assertEqual(2,result['console_title_content'])
        self.assertEqual((19-1)//len(app.CONSOLE_TITLE_SWEEPS)+1,result['console_title_shape'])
        self.assertEqual((19-1)%len(app.CONSOLE_TITLE_SWEEPS)+1,result['console_title_coloring'])
        loader.assert_not_called()

    def test_next_publication_immediately_reflects_control_and_default_changes(self):
        ns=dict(console_title_style=1,console_title_content=1,
                CONSOLE_TITLE_SWEEPS=app.CONSOLE_TITLE_SWEEPS)
        for style in range(1,len(app.CONSOLE_TITLE_NAMES)+1):
            for content in range(1,len(app.CONSOLE_TITLE_CONTENTS)+1):
                ns.update(console_title_style=style,console_title_content=content)
                result=eval(self.expression,ns)
                self.assertEqual(style,result['console_title_style'])
                self.assertEqual(content,result['console_title_content'])
                reconstructed=(result['console_title_shape']-1)*len(app.CONSOLE_TITLE_SWEEPS)+result['console_title_coloring']
                self.assertEqual(style,reconstructed)

    def test_periodic_publish_has_no_hidden_bulk_setting_reads(self):
        calls=[n.func.id for n in ast.walk(self.publish) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertNotIn('load_player_settings',calls)
        names={k.arg for k in self.publish.keywords}
        self.assertTrue({'playing','paused','position_seconds','lyric','lyric_timeline',
                         'lyric_clock_epoch','volume','speed','visualizer_perf'}.issubset(names))


if __name__=='__main__':unittest.main()
