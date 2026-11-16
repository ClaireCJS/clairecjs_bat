import importlib.util,json,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v671_dj',root/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
    def wait(self,c):
        deadline=time.monotonic()+3
        while c.working is not None and time.monotonic()<deadline:time.sleep(.005)
        self.assertIsNone(c.working)

    def test_segments_remember_dialogue_and_include_tracks_finished_during_prefetch(self):
        r=SimpleNamespace(settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None)
        calls=[]
        def synth(history,opts,stage,valid,on_dialogue=None):
            calls.append((list(history),dict(opts)))
            on_dialogue([(1,'A fresh conversation '+str(len(calls)))])
            return ['segment.wav'],''
        with mock.patch.object(dj,'synthesize',synth),mock.patch.object(dj,'append_talk_log'):
            c=dj.Controller(r,producer=synth);c.configure({'enabled':True,'interval':2})
            c.record('Band','One');self.wait(c)
            c.record('Band','Two');self.assertEqual(['segment.wav'],c.take())
            c.record('Band','Three');self.wait(c)
            self.assertEqual(2,len(calls));self.assertEqual(2,calls[1][1]['_new_track_count'])
            self.assertEqual('A fresh conversation 1',calls[1][1]['_recent_dialogues'][0][0]['text'])
            self.assertEqual(['One','Two','Three'],[x['title'] for x in calls[1][0]])

    def test_provider_gets_distinct_new_tracks_and_recent_dialogue(self):
        history=[{'artist':'A','title':'Old'},{'artist':'B','title':'New'}]
        opts=dj.settings({'text_provider':'openrouter'});opts['_new_track_count']=1;opts['_recent_dialogues']=[[{'speaker':1,'text':'previous segment'}]]
        calls=[]
        def post(url,data,headers=None,timeout=45):
            calls.append(data);return {'choices':[{'message':{'content':'[{"speaker":1,"text":"A new angle"}]'}}]}
        with mock.patch.object(dj,'provider_key',return_value='key'),mock.patch.object(dj,'openai_key',return_value=''),mock.patch.object(dj,'post_json',side_effect=post):
            dj.dialogue(history,opts)
        system,user=calls[0]['messages'];context=json.loads(user['content'])
        self.assertEqual([history[-1]],context['new_tracks_since_last_dj']);self.assertEqual(history,context['recent_tracks'])
        self.assertEqual('previous segment',context['recent_dialogues'][0][0]['text']);self.assertIn('not an upcoming playlist',system['content'])

    def test_identical_script_falls_through_to_next_provider(self):
        opts=dj.settings({'gemini_free_confirmed':True});opts['_recent_dialogues']=[[{'speaker':1,'text':'Same conversation again'}]]
        def key(name):return 'key'
        with mock.patch.object(dj,'openai_key',return_value=''),mock.patch.object(dj,'provider_key',side_effect=key),mock.patch.object(dj,'_chat_dialogue',return_value=[(1,'Same conversation again')]),mock.patch.object(dj,'_gemini_dialogue',return_value=[(1,'Something genuinely different')]) as fallback:
            lines,notice=dj.dialogue([{'artist':'A','title':'B'}],opts)
        self.assertEqual([(1,'Something genuinely different')],lines);fallback.assert_called_once();self.assertIn('gemini',notice)

    def test_duplicate_detection_ignores_minor_punctuation(self):
        previous=[[{'speaker':1,'text':'Hello, world!'}]]
        with self.assertRaises(ValueError):dj.reject_repeated_dialogue([(1,'Hello world')],previous)
        self.assertEqual([(1,'A new topic')],dj.reject_repeated_dialogue([(1,'A new topic')],previous))

if __name__=='__main__':unittest.main()
