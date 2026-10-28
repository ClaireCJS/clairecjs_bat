import io
import json
import types
import unittest
from pathlib import Path
from unittest import mock
from PIL import Image
import PAFPlayer as p
import PAFPlayer_workflows as w
import PAFPlayer_web_workflows as web
from PAFPlayer_instance import Instance, resolve_request
from PAFPlayer_windows_media import Bridge,settings,presentation,artwork_bytes
from test_PAFPlayer_workflows import Base,fixture


class ReleaseTests(Base):
    def test_instance_acknowledges_files_folders_regex_playlist_and_rejects_invalid(self):
        self.runtime.app=p
        one=fixture(self.root,'B.wav');two=fixture(self.root,'A.wav')
        playlist=self.root/'songs.m3u8';playlist.write_text(str(one)+'\n'+str(two)+'\n',encoding='utf-8')
        request=resolve_request(self.runtime,[self.root]);self.assertEqual([str(two),str(one)],request['paths'])
        request=resolve_request(self.runtime,[],regex=r'[AB]\.wav$',filelist=playlist)
        self.assertEqual([str(one),str(two)],request['paths'])
        self.assertEqual(str(playlist),resolve_request(self.runtime,[playlist])['playlist'])
        for target in (self.root/'missing.mp3',self.root/'missing.m3u8',self.root/'missing-folder'):
            with self.assertRaises(ValueError):resolve_request(self.runtime,[target])
        with self.assertRaises(ValueError):resolve_request(self.runtime,[],regex='never-matches',filelist=playlist)
        with self.assertRaises(ValueError):resolve_request(self.runtime,[],regex='.*',filelist=self.root/'absent.txt')
        state={'entries':[str(one)],'next':[],'current':str(one),'playlist':None,'reason':'fixture'}
        self.runtime.queue_read=lambda:dict(state)
        def edit(payload):
            result=web.calculate_queue_edit(self.runtime,state,payload);state.clear();state.update(result)
            return web.queue_snapshot(self.runtime)
        self.runtime.queue_bridge=edit
        owner=Instance(self.runtime);self.assertTrue(owner.acquire());owner.start()
        try:
            other=Instance(self.runtime);self.assertFalse(other.acquire())
            result=other.forward({'paths':[str(two)],'playlist':None})
            self.assertTrue(result['ok']);self.assertEqual([str(two)],state['next'])
            other.forward(resolve_request(self.runtime,[playlist]))
            self.assertEqual(str(playlist),state['playlist']);self.assertEqual([str(one),str(two)],state['entries'])
            with self.assertRaises(ValueError):other.forward({'paths':[str(self.root/'absent.wav')],'playlist':None})
        finally:owner.close()
        replacement=Instance(self.runtime);self.assertTrue(replacement.acquire());replacement.close()

    def test_windows_settings_titles_transport_and_derived_artwork(self):
        self.runtime.app=p;bridge=self.runtime.windows_media
        state={'metadata':{'Artist':'Test artist','Song':'Test song','Album':'Album'},'duration_seconds':100,'position_seconds':40,'playing':True}
        original=json.dumps(state)
        image=Image.new('RGB',(4,4),(200,100,50));stream=io.BytesIO();image.save(stream,format='PNG');source=stream.getvalue()
        server=mock.Mock();server.snapshot.return_value=state;server.art_snapshot.return_value=(source,'image/png');self.runtime.server=server
        options=settings(self.runtime);self.assertFalse(options['enabled'])
        for preset,title in [('artist-song','Test artist — Test song'),('song-artist','Test song — Test artist'),('song','Test song'),('paf-artist-song','PAFPlayer: Test artist — Test song')]:
            options['title_format']=preset;self.assertEqual(title,presentation(state,options)['title'])
        options.update(enabled=True,brightness=50);self.runtime.settings['windows_media']=options
        derived=artwork_bytes(self.runtime,options)
        with Image.open(io.BytesIO(derived)) as result:self.assertEqual((100,50,25),result.getpixel((0,0)))
        self.assertEqual(source,server.art_snapshot()[0]);self.assertEqual(original,json.dumps(state))
        bridge.command('seek',50);server.enqueue_action.assert_called_with(p.WEB_SEEK_RATIO_PREFIX+'0.5')
        bridge.command('next');server.enqueue_action.assert_called_with(p.NEXT_FILE)
        options['previous_next']=False;server.enqueue_action.reset_mock();bridge.command('next');server.enqueue_action.assert_not_called()
        options['source']='none';self.assertIsNone(artwork_bytes(self.runtime,options))
        options['enabled']=False;bridge.tick();self.assertEqual('Disabled',bridge.status['state'])

    def test_windows_unavailable_is_clear_and_does_not_change_console(self):
        bridge=self.runtime.windows_media
        self.runtime.settings['windows_media']={'enabled':True}
        with mock.patch.object(bridge,'connect',side_effect=ImportError('test missing backend')):
            bridge.start()
            for _ in range(100):
                if bridge.status['state']=='Unavailable':break
                bridge.stop.wait(.01)
            bridge.close()
        self.assertEqual('Unavailable',bridge.status['state']);self.assertIn('PyWinRT',bridge.status['reason']);self.assertFalse(bridge.active)

    def test_throb_action_validation_and_tooltip_newlines(self):
        for key in ('artist_throb_ms','song_throb_ms'):
            self.assertTrue(p.paf_web_action_is_allowed('web-set:'+key+':100'))
            self.assertTrue(p.paf_web_action_is_allowed('web-set:'+key+':60000'))
            self.assertFalse(p.paf_web_action_is_allowed('web-set:'+key+':99'))
            self.assertFalse(p.paf_web_action_is_allowed('web-set:'+key+':60001'))
        page=p._paf_web_html();line=next(x for x in page.splitlines() if 'const orderTip=' in x)
        self.assertIn(r'\n\nCURRENT MODE',line);self.assertNotIn(r'\\n',line)


if __name__=='__main__':unittest.main()
