from datetime import datetime
import importlib.util
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v667_talk_log',root/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
    def test_format_order_unicode_gender_and_append(self):
        path=Path(tempfile.mkdtemp(prefix='paf-talk-test-'))/'nested'/'dj.log'
        history=[{'artist':'Björk','title':'Earlier'}, {'artist':'Band','title':'Newest'}]
        lines=[(1,'Hello there'),(2,'Good\nmorning')]
        dj.append_talk_log(history,lines,dj.settings(),path,datetime(2026,11,12,12,53))
        first=path.read_text(encoding='utf8')
        self.assertEqual(first,'━━━━━━━━━━━━━━━━━━━━━━\n\n⭐DATE:  20261112  12:53PM\n\n⛧LAST SONG #1: Band - Newest\n⛧LAST SONG #2: Björk - Earlier\n\n👩🗣️ Hello there\n👨🗣️ Good morning\n\n')
        dj.append_talk_log(history,lines,dj.settings(),path,datetime(2026,11,12,12,54))
        both=path.read_text(encoding='utf8');self.assertTrue(both.startswith(first));self.assertEqual(2,both.count('━━━━━━━━━━━━━━━━━━━━━━'))

    def runtime(self):
        return SimpleNamespace(root=Path(tempfile.mkdtemp(prefix='paf-talk-controller-')),settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None)

    def test_generated_text_logged_even_if_speech_fails(self):
        path=Path(tempfile.mkdtemp(prefix='paf-talk-output-'))/'dj.log'
        c=dj.Controller(self.runtime())
        with mock.patch.object(dj,'DJ_TALK_LOG_PATH',path), mock.patch.object(dj,'dialogue',return_value=([(1,'First line'),(2,'Reply')],'')), mock.patch.object(dj,'speech_openai',side_effect=RuntimeError('offline')), mock.patch.object(dj,'ensure_piper',side_effect=dj.PiperSetupError('offline')):
            self.assertTrue(c.start(True,current={'artist':'Band','title':'Track'}))
            deadline=time.monotonic()+3
            while c.working is not None and time.monotonic()<deadline:time.sleep(.005)
        self.assertIsNone(c.working);self.assertIn('⛧LAST SONG #1: Band - Track',path.read_text(encoding='utf8'))
        self.assertIn('👨🗣️ Reply',path.read_text(encoding='utf8'));self.assertTrue(c.error)
        self.assertEqual([(1,'First line'),(2,'Reply')],c.commentary)

    def test_log_failure_is_visible_and_generation_continues(self):
        c=dj.Controller(self.runtime())
        with mock.patch.object(dj,'append_talk_log',side_effect=PermissionError('denied')), mock.patch.object(dj,'dialogue',return_value=([(1,'Still talking')],'')), mock.patch.object(dj,'speech_openai'):
            self.assertTrue(c.start(True,current={'artist':'Band','title':'Track'}))
            deadline=time.monotonic()+3
            while c.working is not None and time.monotonic()<deadline:time.sleep(.005)
        self.assertIsNone(c.working);self.assertTrue(c.ready);self.assertIn('could not be written',c.help_snapshot()[3]);self.assertIn('could not be written',' '.join(c.warning_messages()))

if __name__=='__main__':unittest.main()
