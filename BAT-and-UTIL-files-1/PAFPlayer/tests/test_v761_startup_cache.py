import json,os,sys,subprocess,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
import PAFPlayer as app
from PAFPlayer_startup_cache import AnalysisCache,audio_worker_command

class StartupCacheTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='v761-',dir=Path('tests/runs').resolve()))
        self.audio=self.root/'track.wav';self.audio.write_bytes(b'fixture')
        self.cache=AnalysisCache(self.root/'runtime/cache/analysis')
        self.patches=[patch.object(app,'track_analysis_cache',return_value=self.cache)]
        for item in self.patches:item.start()
        app._AUDIO_METADATA_CACHE.clear();app._EDGE_SILENCE_BOUNDS_CACHE.clear()
    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        app.set_post_playback_output(False)
    def test_metadata_reused_after_memory_cache_is_cleared(self):
        payload={'format':{'duration':'4','tags':{'title':'test','artist':'artist','REPLAYGAIN_TRACK_GAIN':'-3 dB'}},'streams':[{'channels':2,'channel_layout':'stereo'}]}
        with patch.object(app,'ffprobe_executable',return_value=Path('ffprobe.exe')),patch.object(app.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(payload))) as run:
            first=app.probe_audio_metadata(self.audio);app._AUDIO_METADATA_CACHE.clear();second=app.probe_audio_metadata(self.audio)
            self.assertEqual(first,second);self.assertEqual(1,run.call_count)
            self.assertEqual((2,'stereo'),app.probe_audio_stream_layout(self.audio))
    def test_audio_file_timestamp_change_invalidates_metadata(self):
        result=SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'4'},'streams':[]}))
        with patch.object(app,'ffprobe_executable',return_value=Path('ffprobe.exe')),patch.object(app.subprocess,'run',return_value=result) as run:
            app.probe_audio_metadata(self.audio);app._AUDIO_METADATA_CACHE.clear()
            stamp=self.audio.stat().st_mtime_ns+2000000000;os.utime(self.audio,ns=(stamp,stamp))
            app.probe_audio_metadata(self.audio);self.assertEqual(2,run.call_count)
    def test_silence_analysis_reused_with_identical_bounds(self):
        result=SimpleNamespace(returncode=0,stderr='[silencedetect] silence_start: 0\n[silencedetect] silence_end: 1 | silence_duration: 1\n')
        with patch.object(app,'paf_ffmpeg_tool_path',return_value='ffmpeg.exe'),patch.object(app.subprocess,'run',return_value=result) as run:
            first=app.detect_edge_silence_bounds(self.audio,4,enabled=True);app._EDGE_SILENCE_BOUNDS_CACHE.clear()
            second=app.detect_edge_silence_bounds(self.audio,4,enabled=True)
            self.assertEqual(first,second);self.assertGreater(first[0],0);self.assertEqual(1,run.call_count)
    def test_trim_parameters_invalidate_silence_cache(self):
        with patch.object(app,'paf_ffmpeg_tool_path',return_value='ffmpeg.exe'),patch.object(app.subprocess,'run',return_value=SimpleNamespace(returncode=0,stderr='')) as run:
            app.detect_edge_silence_bounds(self.audio,4,enabled=True,keep_seconds=.1);app._EDGE_SILENCE_BOUNDS_CACHE.clear()
            app.detect_edge_silence_bounds(self.audio,4,enabled=True,keep_seconds=.2);self.assertEqual(2,run.call_count)
    def test_failed_scans_are_not_persisted(self):
        with patch.object(app,'paf_ffmpeg_tool_path',return_value='ffmpeg.exe'),patch.object(app.subprocess,'run',return_value=SimpleNamespace(returncode=1,stderr='bad input')) as run:
            app.detect_edge_silence_bounds(self.audio,4,enabled=True);app._EDGE_SILENCE_BOUNDS_CACHE.clear()
            app.detect_edge_silence_bounds(self.audio,4,enabled=True);self.assertEqual(2,run.call_count)
        self.assertFalse(list((self.cache.root/'silence').glob('*/*.json')))
    def test_corrupt_or_unwritable_cache_is_disposable(self):
        key=self.cache.key(self.audio,[]);folder=self.cache.root/'metadata'/key;folder.mkdir(parents=True)
        (folder/'bad.json').write_text('bad json',encoding='utf-8')
        self.assertIsNone(self.cache.read('metadata',key));self.cache.write('metadata',key,{'fine':True})
        self.assertEqual({'fine':True},self.cache.read('metadata',key))
        denied=AnalysisCache(self.audio);denied.write('metadata',key,{});self.assertIsNone(denied.read('metadata',key))
    def test_first_worker_launch_builds_in_background_and_preserves_module_identity(self):
        script=self.root/'player.py';script.write_text("import sys,json,__main__\nmarker=42\nassert __main__.marker==42\nprint(json.dumps([__file__,sys.argv[1:]]))\n",encoding='utf-8')
        started=time.perf_counter();first=audio_worker_command(script)
        self.assertLess(time.perf_counter()-started,1)
        self.assertEqual(str(script),first[-2])
        cache=script.parent/'runtime/cache/worker-code';deadline=time.monotonic()+10
        while not list(cache.glob('*/*.pyc')) and time.monotonic()<deadline:time.sleep(.02)
        second=audio_worker_command(script);self.assertIn('-c',second)
        result=subprocess.run(second,check=True,capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual([str(script),['--paf-audio-worker']],json.loads(result.stdout))
    def test_warm_worker_cache_is_reused_without_replacement(self):
        script=self.root/'minimal.py';script.write_text('pass\n',encoding='utf-8')
        audio_worker_command(script);deadline=time.monotonic()+10;folder=script.parent/'runtime/cache/worker-code'
        while not list(folder.glob('*/*.pyc')) and time.monotonic()<deadline:time.sleep(.02)
        before={str(p):p.stat().st_mtime_ns for p in folder.glob('*/*.pyc')};audio_worker_command(script)
        self.assertEqual(before,{str(p):p.stat().st_mtime_ns for p in folder.glob('*/*.pyc')})
    def test_bundle_matches_source(self):
        self.assertEqual(Path('src/PAFPlayer_startup_cache.py').read_text(encoding='utf-8-sig'),app._PAF_BUNDLED_SOURCES['PAFPlayer_startup_cache'])

if __name__=='__main__':unittest.main()
