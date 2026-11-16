import importlib.util
from pathlib import Path
import threading
import time
import unittest
from types import SimpleNamespace
from unittest import mock

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('v666_dj', root/'src/PAFPlayer_dj.py')
dj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
    def runtime(self):
        return SimpleNamespace(settings={}, lock=threading.RLock(), stop_event=threading.Event(), save_settings=lambda:None)

    def ready(self, c):
        deadline = time.monotonic()+2
        while c.working is not None and time.monotonic()<deadline:
            time.sleep(.005)
        self.assertIsNone(c.working)

    def test_defaults_and_saved_voice_choices(self):
        self.assertEqual((1,1), (dj.settings()['women'],dj.settings()['men']))
        self.assertEqual(['marin','cedar'],dj.settings()['voices'].split(',')[:2])
        saved=dj.settings({'speakers':2,'women':2,'men':0})
        self.assertEqual((2,0),(saved['women'],saved['men']))

    def test_force_generates_and_is_due_during_both_sleep_reasons(self):
        for reason in ('screen locked','scheduled sleep'):
            with self.subTest(reason=reason):
                c=dj.Controller(self.runtime(),lambda *args: (['voice.wav'],''))
                c.sleep_status=lambda:(reason,'')
                self.assertFalse(c.start(False,current={'artist':'a','title':'b'}))
                self.assertTrue(c.start(True,current={'artist':'a','title':'b'}))
                self.ready(c)
                self.assertEqual(['voice.wav'],c.ready)
                self.assertTrue(c.due())
                self.assertEqual(['voice.wav'],c.take())
                self.assertTrue(c.play_forced)

    def test_forced_playback_continues_when_sleeping(self):
        c=dj.Controller(self.runtime(),lambda *args: (['voice.wav'],''))
        c.sleep_status=lambda:('screen locked','')
        c.start(True,current={'artist':'a','title':'b'});self.ready(c)
        files=c.take();finished=threading.Event();terminated=threading.Event()
        class Process:
            def poll(self):return 0 if finished.is_set() else None
            def terminate(self):terminated.set();finished.set()
        with mock.patch.object(dj.subprocess,'Popen',return_value=Process()):
            self.assertTrue(c.play(files,'ffplay'));time.sleep(.25)
            self.assertFalse(terminated.is_set());self.assertFalse(c.play_done)
            finished.set();c.play_thread.join(2)
        self.assertTrue(c.play_done);self.assertFalse(terminated.is_set())

    def test_force_joins_preparing_automatic_job_through_sleep(self):
        started=threading.Event();gate=threading.Event();asleep=[False]
        def producer(*args):started.set();gate.wait(2);return ['voice.wav'],''
        c=dj.Controller(self.runtime(),producer);c.configure({'enabled':True})
        c.sleep_status=lambda:('scheduled sleep' if asleep[0] else '', '')
        c.history.append({'artist':'a','title':'b'});c.count=1
        self.assertTrue(c.start(False));self.assertTrue(started.wait(1))
        asleep[0]=True
        self.assertTrue(c.start(True));gate.set();self.ready(c)
        self.assertTrue(c.due());self.assertEqual(['voice.wav'],c.take())

if __name__=='__main__':unittest.main()
