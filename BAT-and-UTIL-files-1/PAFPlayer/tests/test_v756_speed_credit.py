import ast,inspect,io,sys,threading,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import PAFPlayer as app
import PAFPlayer_dj as dj

class SpeedCreditTests(unittest.TestCase):
    def controller(self,**state):
        c=dj.Controller.__new__(dj.Controller)
        c.options={'enabled':True,'text_precedence':['openai','ollama'],'speech_provider':'piper'}
        c.stage='Ready';c.error='';c.ready=['speech.wav'];c.working=None
        c.warning_messages=lambda:[dj.OPENAI_CREDIT_WARNING,'unrelated warning']
        for name,value in state.items():setattr(c,name,value)
        return c
    def test_credit_is_minor_when_off_successful_pending_or_not_in_chain(self):
        cases=[{}, {'options':{'enabled':False,'text_precedence':['openai'],'speech_provider':'auto'},'stage':'Failed','error':'failed','ready':None},
          {'options':{'enabled':True,'text_precedence':['ollama'],'speech_provider':'piper'},'stage':'Failed','error':'failed','ready':None},
          {'stage':'Failed','error':'failed','ready':None,'working':123}]
        for state in cases:
            with self.subTest(state=state):
                c=self.controller(**state)
                self.assertNotIn(dj.OPENAI_CREDIT_WARNING,c.hud_warning_messages())
                self.assertIn(dj.OPENAI_CREDIT_WARNING,c.warning_messages())
                self.assertIn('unrelated warning',c.hud_warning_messages())
    def test_failed_enabled_chain_escalates(self):
        c=self.controller(stage='Failed',error='all providers failed',ready=None)
        self.assertIn(dj.OPENAI_CREDIT_WARNING,c.hud_warning_messages())
    def test_no_ai_suppresses_credit_escalation(self):
        c=self.controller(stage='Failed',error='all providers failed',ready=None)
        with patch.object(dj,'AI_DISABLED',True):
            self.assertNotIn(dj.OPENAI_CREDIT_WARNING,c.hud_warning_messages())
    def test_help_does_not_repeat_minor_credit_warning(self):
        c=self.controller();c.help_snapshot=lambda:([], 'Ready','', '', True);c.log=None
        text=' '.join(app.dj_help_rows(c,120))
        self.assertNotIn(dj.OPENAI_CREDIT_WARNING,text)
        self.assertIn('unrelated warning',text)
    def test_warning_filter_is_local_and_fast(self):
        c=self.controller()
        with patch.object(dj,'provider_key',side_effect=AssertionError('No key I/O')),patch.object(dj,'post_json',side_effect=AssertionError('No network')):
            start=time.monotonic();c.hud_warning_messages();self.assertLess(time.monotonic()-start,.1)
    def test_menu_distinguishes_playing_from_pending(self):
        node=next(n for n in ast.walk(ast.parse(inspect.getsource(app.play_audio_file))) if isinstance(n,ast.FunctionDef) and n.name=='speed_entry_screen')
        keyboard=Mock();keyboard.kbhit.return_value=True;keyboard.getwch.side_effect=list('1.333\r')
        render=Mock();env={'os':app.os,'current_speed':lambda:1.1,'render_catalog_prompt':render,'SPEED_SET_PREFIX':app.SPEED_SET_PREFIX,'parse_speed_entry_value':app.parse_speed_entry_value}
        with patch.dict(sys.modules,{'msvcrt':keyboard}):
            exec(compile(ast.Module(body=[node],type_ignores=[]),'<menu>','exec'),env)
            self.assertEqual(app.SPEED_SET_PREFIX+'1.333',env['speed_entry_screen']())
        self.assertIn('Playing: 1.1×   Pending: 1.333',render.call_args.args[0][2])
        self.assertIn('Enter applies',render.call_args.args[0][2])
    def test_1333_reaches_decoder_and_hud_after_enter(self):
        from test_v742_simple_splash import SimpleSplashTests
        original=app.play_audio_file;custom=[None];calls=[0]
        def key():
            calls[0]+=1
            return app.SPEED_ENTRY if calls[0]==1 else app.STOP
        def play(*args,**kwargs):
            kwargs['custom_speed_state']=custom;kwargs['key_action_reader']=key
            return original(*args,**kwargs)
        keyboard=Mock();keyboard.kbhit.return_value=True;keyboard.getwch.side_effect=list('1.333\r')
        with patch.object(app,'play_audio_file',side_effect=play),patch.dict(sys.modules,{'msvcrt':keyboard}),patch.object(app,'ffplay_command',wraps=app.ffplay_command) as decoder:
            result,_,output=SimpleSplashTests().run_preview(True)
        self.assertEqual('stopped',result);self.assertEqual(1.333,custom[0])
        self.assertTrue(any('1.333' in repr(call) for call in decoder.call_args_list))
        last_menu=max(i for i,text in enumerate(output) if 'Pending: 1.333' in text)
        self.assertTrue(any('\033[2K' in text for text in output[last_menu+1:]))
        self.assertFalse(any('\033[2J' in text for text in output))
        self.assertEqual('1.333×',app.format_speed(custom[0]))
        source=inspect.getsource(original)
        self.assertIn('stop_process(process)\n                        redraw_entire_player_ui(position, indicator, clear_art=False)\n                        break',source)
    def test_bundle_matches_dj_source(self):
        self.assertEqual(Path('src/PAFPlayer_dj.py').read_text(encoding='utf-8-sig'),app._PAF_BUNDLED_SOURCES['PAFPlayer_dj'])

if __name__=='__main__':unittest.main()
