import importlib.util
import json
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dj_v660_candidate', ROOT/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
    def runtime(self):
        return SimpleNamespace(root=Path(tempfile.mkdtemp(prefix='paf-dj-logs-test-')),
                               settings={}, lock=threading.RLock(), stop_event=threading.Event(),
                               save_settings=lambda:None)

    def test_wait_status_and_decision_log_do_not_include_track_data(self):
        runtime=self.runtime(); controller=dj.Controller(runtime,lambda *a:(['audio'],''))
        controller.configure({'enabled':True,'interval':3})
        controller.record('SECRET ARTIST', 'SECRET SONG')
        self.assertIn('1/3',controller.help_snapshot()[1])
        events=[json.loads(x) for x in controller.log.path.read_text().splitlines()]
        self.assertTrue(any(e['event']=='job.skipped' and e.get('reason')=='interval' for e in events))
        self.assertNotIn('SECRET',str(events))

    def test_job_failure_logs_error_type_without_sensitive_exception_text(self):
        runtime=self.runtime()
        def fail(*args): raise RuntimeError('sk-secret-EXAMPLE private text')
        controller=dj.Controller(runtime,fail)
        controller.start(True,current={'artist':'private','title':'track'})
        deadline=time.monotonic()+2
        while controller.working is not None and time.monotonic()<deadline:time.sleep(.005)
        data=controller.log.path.read_text()
        self.assertIn('job.failed',data);self.assertIn('RuntimeError',data)
        self.assertNotIn('sk-secret',data);self.assertNotIn('private',data)

    def test_provider_failure_records_http_status_not_body(self):
        events=[];dj._DJ_THREAD_CONTEXT.log=lambda name,**kw:events.append((name,kw))
        error=urllib.error.HTTPError('https://example.test',401,'private secret',{},None)
        def request(url,*args,**kw):
            if 'openai' in url:raise error
            return {'message':{'content':'[{"speaker":1,"text":"hello"}]'}}
        try:
            with mock.patch.dict(dj.os.environ,{'OPENAI_API_KEY':'example-secret'}), mock.patch.object(dj,'post_json',side_effect=request):
                dj.dialogue([{'artist':'a','title':'b'}],dj.settings({'ollama_model':'demo'}))
        finally:dj._DJ_THREAD_CONTEXT.log=None
        self.assertTrue(any(e[0]=='text.provider.fallback' and e[1].get('http_status')==401 for e in events))
        self.assertNotIn('secret',str(events))

    def test_automatic_job_stage_is_visible_in_status(self):
        gate=threading.Event();controller=dj.Controller(self.runtime(),lambda *a:(gate.wait(2) and ['ok'],''))
        controller.configure({'enabled':True});controller.record('a','b')
        self.assertEqual('Preparing',controller.status()['stage'])
        gate.set()

if __name__=='__main__':unittest.main()
