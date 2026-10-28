import io
import json
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from PIL import Image
import PAFPlayer as p
import PAFPlayer_workflows as w
from PAFPlayer_discord import Publisher, public_content
from PAFPlayer_cuda_benchmarks import Benchmark, analyze
from PAFPlayer_render_book import render_song
from test_PAFPlayer_workflows import fixture, Base


class IntegrationTests(Base):
    def test_monitor_mode_change_imports_existing_stable_file(self):
        song=fixture(self.root)
        first=w.FolderMonitor(self.runtime,[self.root],'index')
        first.scan(now=0); first.scan(now=3)
        target=self.root/'monitored.m3u8'
        second=w.FolderMonitor(self.runtime,[self.root],'playlist',str(target))
        second.scan(now=4); second.scan(now=7)
        self.assertIn(str(song),target.read_text())
        again=w.FolderMonitor(self.runtime,[self.root],'playlist',str(target))
        self.assertEqual([],again.scan(now=20))

    def discord_fixture(self):
        self.state={'playing':True,'track':{'title':'Hello @everyone','artist':'Fixture'}}
        self.runtime.server=types.SimpleNamespace(snapshot=lambda:self.state,current_audio=lambda:self.root/'local.wav')
        self.runtime.settings.update(discord_enabled=True,discord_share_local_titles=True)
        publisher=Publisher(self.runtime)
        response=mock.MagicMock();response.__enter__.return_value.read.return_value=b'{"id":"123"}'
        publisher.opener=mock.Mock();publisher.opener.open.return_value=response
        return publisher

    @mock.patch.dict('os.environ',{'PAFPLAYER_DISCORD_WEBHOOK':'https://discord.com/api/webhooks/123/fake-token'})
    def test_discord_optin_privacy_rate_limit_and_updates(self):
        publisher=self.discord_fixture()
        self.runtime.settings['discord_share_local_titles']=False
        publisher.tick(now=0);publisher.opener.open.assert_not_called()
        self.runtime.settings['discord_share_local_titles']=True
        publisher.tick(now=1)
        request=publisher.opener.open.call_args.args[0]
        self.assertNotIn('@everyone',request.data.decode())
        self.assertEqual([],json.loads(request.data)['allowed_mentions']['parse'])
        self.state['paused']=True;publisher.tick(now=2)
        self.assertEqual(1,publisher.opener.open.call_count)
        publisher.tick(now=17);self.assertEqual('PATCH',publisher.opener.open.call_args.args[0].method)
        self.state['private']=True;publisher.tick(now=34)
        self.assertEqual('PAFPlayer — private playback',json.loads(publisher.opener.open.call_args.args[0].data)['content'])
        self.state['private']=False
        publisher.opener.open.side_effect=HTTPError('https://discord.com',429,'rate',{},io.BytesIO(b'{"retry_after":120}'))
        publisher.tick(now=50);self.assertEqual(170,publisher.next_send)
        self.assertNotIn('fake-token',str(self.app.append_pafplayer_trace.call_args_list))

    def test_benchmark_alternates_and_mismatch_keeps_cpu(self):
        path=self.root/'benchmark.jsonl'
        with mock.patch.object(Benchmark,'_initialize'):
            b=Benchmark(path)
        b.cp=object();b.reason='';b.good=3
        bottom=Image.new('RGBA',(16,16),'red');top=Image.new('RGBA',(16,16),(0,0,255,128))
        expected=Image.alpha_composite(bottom,top)
        b.cuda_composite=lambda *args:(expected.copy(),{'gpu_ms':.1,'upload_ms':.1,'download_ms':.1})
        window=types.SimpleNamespace(after_idle=lambda fn:fn())
        for offset in (0,11):
            b.started=time.perf_counter()-offset
            image=b.composite(bottom,top,workload='floating-lyrics');b.present(image,window)
        b.cuda_composite=lambda *args:(Image.new('RGBA',(16,16),'green'),{})
        b.present(b.composite(bottom,top,workload='floating-lyrics'),window)
        b.close()
        rows=[json.loads(x) for x in path.read_text().splitlines()]
        frames=[x for x in rows if x['kind']=='frame']
        self.assertEqual(['cpu','cuda','cpu'],[x['visible'] for x in frames])
        self.assertTrue(frames[-1]['mismatch_pixels'])
        result=analyze(path);self.assertIn('Correctness mismatch; CPU retained',result['fallback_reasons'])
        self.assertIsNone(next(iter(result['workloads'].values()))['cuda_improves_observed_end_to_end'])

    def test_render_real_timestamps_self_contained_deterministic_and_recycle_decline(self):
        song=fixture(self.root)
        song.with_suffix('.lrc').write_text('[00:00.20]First lyric\n[00:01.00]Second lyric\n',encoding='utf-8')
        Image.new('RGB',(100,100),'teal').save(self.root/'cover.png')
        self.runtime.app=p
        with mock.patch.object(p,'append_pafplayer_trace'):
            result=render_song(self.runtime,song,output=self.root/'book',open_browser=False,prompt=False,prefix='review')
            other=render_song(self.runtime,song,output=self.root/'book2',open_browser=False,prompt=False,prefix='review')
            self.assertEqual(2,result['images'])
            html=Path(result['book']).read_text(encoding='utf-8')
            self.assertIn('0.200s',html);self.assertIn('1.000s',html);self.assertIn('data:image/png;base64,',html)
            self.assertEqual((Path(result['directory'])/'review-0001.png').read_bytes(),(Path(other['directory'])/'review-0001.png').read_bytes())
            with mock.patch('builtins.input',return_value='n'),mock.patch('PAFPlayer_render_book.recycle') as recycle:
                declined=render_song(self.runtime,song,open_browser=False)
                self.assertFalse(declined['saved']);recycle.assert_called_once()

    def test_learned_final_component_and_hud_shortcuts(self):
        for title in ('Mom Goddess (live) (youtube-rip)',"A Song (' )",'Ends .*'):
            selector=p.normalized_learned_title_selector(title)
            self.assertFalse(selector.endswith('.*'))
        self.assertEqual(p.HUD_DETAILS_TOGGLE,p.interpret_console_key('h',ctrl=True))
        self.assertEqual(p.HUD_DETAILS_TOGGLE,p.interpret_console_key('\x08',ctrl=True))
        self.assertEqual(p.HUD_DETAILS_TOGGLE,p.interpret_console_key('\x1f',ctrl=True,alt=True))


if __name__=='__main__':unittest.main()
