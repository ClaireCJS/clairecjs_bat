import ast,inspect,sys,unittest
from unittest.mock import Mock,patch
import PAFPlayer as app

class SpeedEntryTests(unittest.TestCase):
    def test_x_opens_speed_instead_of_stopping(self):
        self.assertEqual(app.SPEED_ENTRY,app.interpret_console_key('x'))
        self.assertEqual(app.SPEED_ENTRY,app.interpret_console_key('X',shift=True))

    def test_multiplier_parser(self):
        for text,speed in [('4',4),('4x',4),('1.25',1.25),('0.5',.5),('=',1),('1.37',1.37),('0.75x',.75),('2.333',2.333),('999',999),('1e-2',.01)]:
            self.assertEqual(app.parse_speed_entry_value(text),speed)
        for text in ('','NaN','inf','0','-1','4xxx'):
            self.assertIsNone(app.parse_speed_entry_value(text))

    def menu(self,keys):
        tree=ast.parse(inspect.getsource(app.play_audio_file))
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='speed_entry_screen')
        fake=Mock();fake.kbhit.return_value=True;fake.getwch.side_effect=list(keys)
        env={'os':app.os,'speed_index':app.PLAYBACK_SPEEDS.index(1.0),'PLAYBACK_SPEEDS':app.PLAYBACK_SPEEDS,'render_catalog_prompt':Mock(),'current_speed':lambda:1.0,
            'SPEED_SET_PREFIX':app.SPEED_SET_PREFIX,'parse_speed_entry_value':app.parse_speed_entry_value}
        with patch.dict(sys.modules,{'msvcrt':fake}):
            exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-speed-menu>','exec'),env)
            return env['speed_entry_screen']()

    def test_buffered_four_then_enter_sets_four_x(self):
        result=self.menu('4\r')
        self.assertEqual(result,app.SPEED_SET_PREFIX+str(4.0))

    def test_cancel_and_reset(self):
        self.assertEqual(self.menu('\x1b'),'cancel')
        self.assertEqual(self.menu('='),app.SPEED_SET_PREFIX+str(1.0))

    def test_menu_applies_speed_through_playback_restart_path(self):
        from test_v742_simple_splash import SimpleSplashTests
        original=app.play_audio_file;state=[app.PLAYBACK_SPEEDS.index(1.0)];calls=[0]
        def key():
            calls[0]+=1
            return app.SPEED_ENTRY if calls[0]==1 else app.STOP
        def play(*args,**kwargs):
            kwargs['speed_index_state']=state;kwargs['key_action_reader']=key
            return original(*args,**kwargs)
        fake=Mock();fake.kbhit.return_value=True;fake.getwch.side_effect=['4','\r']
        with patch.object(app,'play_audio_file',side_effect=play),patch.dict(sys.modules,{'msvcrt':fake}):
            result,_,_=SimpleSplashTests().run_preview(True)
        self.assertEqual(result,'stopped')
        self.assertEqual(app.PLAYBACK_SPEEDS[state[0]],4.0)

    def test_nonpreset_multiplier_reaches_decoder_and_survives_next_track(self):
        from test_v742_simple_splash import SimpleSplashTests
        original=app.play_audio_file;state=[app.PLAYBACK_SPEEDS.index(1.0)];custom=[None];calls=[0]
        def key():
            calls[0]+=1
            return app.SPEED_ENTRY if calls[0]==1 else app.STOP
        def play(*args,**kwargs):
            kwargs['speed_index_state']=state;kwargs['custom_speed_state']=custom;kwargs['key_action_reader']=key
            return original(*args,**kwargs)
        fake=Mock();fake.kbhit.return_value=True;fake.getwch.side_effect=list('1.37\r')
        with patch.object(app,'play_audio_file',side_effect=play),patch.dict(sys.modules,{'msvcrt':fake}),patch.object(app,'ffplay_command',wraps=app.ffplay_command) as decoder:
            SimpleSplashTests().run_preview(True)
            self.assertEqual(custom[0],1.37)
            SimpleSplashTests().run_preview(True)
        self.assertEqual(custom[0],1.37)
        self.assertTrue(any('1.37' in repr(call) for call in decoder.call_args_list),repr(decoder.call_args_list))
        self.assertTrue(app.speed_color(1.37,0).startswith('\x1b'))

    def test_menu_accepts_nonpreset_decimal(self):
        self.assertEqual(self.menu('1.37\r'),app.SPEED_SET_PREFIX+'1.37')

    def test_decoder_filter_preserves_custom_float_precision(self):
        value=1.234567891234
        self.assertEqual(float(app.atempo_filter(value).split('=')[1]),value)
