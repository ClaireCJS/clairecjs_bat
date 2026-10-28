"""Exercise delivery ordering, independent clocks, and terminal fallback paths."""
import json
import re
import subprocess
import unittest
from unittest import mock

import play_audio_file as p


class DeliveryTests(unittest.TestCase):
    def test_web_clock_keeps_advancing_while_console_is_busy(self):
        server = object.__new__(p.PAFWebServer)
        data = bytes([10] * 30 * 12 * 10)
        process = mock.Mock(playback_clock={'seconds': 2, 'at': 100, 'queued_seconds': .5})
        process.poll.return_value = None
        process.playback_started_at = 90
        server.publish_timeline((b'', 12, 30), 2, 1, 100)
        server.bind_timeline_clock(process, 0, 1, 90, 10, lambda: (data, 12, 30))
        with mock.patch.object(p.time, 'monotonic', return_value=102):
            process.playback_clock = {'seconds': 4, 'at': 102, 'queued_seconds': .5}
            result = server.timeline_snapshot()
            self.assertEqual(4, result['position'])
            self.assertTrue(result['playing'])
            self.assertTrue(result['frames'])
            process.poll.return_value = 0
            self.assertFalse(server.timeline_snapshot()['playing'])
            server.publish_timeline((data, 12, 30), 3, 0, 102, playing=False)
            self.assertEqual(3, server.timeline_snapshot()['position'])

    def test_tabs_and_newlines_do_not_escape_wrapped_terminal_rows(self):
        self.assertEqual(['alpha beta gamma'], p.wrap_to_cells('alpha\nbeta\tgamma', 80))
        self.assertEqual(['❷   qzx'], p.wrap_to_cells('❷   qzx', 80))

    def test_chafa_fallback_retains_drcs_charset(self):
        with mock.patch.object(p, 'ARTWORK_SEAM_STRATEGY', 4):
            self.assertFalse(p.art_detail_cell_uses_unicode_glyph(1, '!'))
            self.assertTrue(p.art_detail_cell_uses_unicode_glyph(1, '▀'))

    def test_browser_timeline_first_response_does_not_lose_status_metadata(self):
        html = p._paf_web_html()
        js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', html, re.S))
        timeline_start = js.index('async function timelineTick(){')
        timeline_end = js.index('\nfunction drawSpectrum(', timeline_start)
        metadata_start = js.index('  // Status owns metadata')
        metadata_end = js.index('  webLyricTimeline=Array.isArray', metadata_start)
        selection_start = js.index('function timelineSpectrumAt(')
        selection_end = js.index('async function timelineTick', selection_start)
        code = '''const assert=require('node:assert/strict');
let webClockSample={paused:true,duration:0,position:0},spectrumTimeline=null,lastTimelineClockAt=-Infinity,webLyricTimeline=[];
let spectrumTarget=[],spectrumCurrent=[];
let answer={source:'track',position:2,ui_start:0,speed:1,playing:true,clock_epoch:50,frames:'',fps:30,width:12,start_frame:0};
const performance={now:()=>1000},setTimeout=()=>{},document={hidden:false},renderWebLyric=()=>{};
const fetch=async()=>({json:async()=>({...answer}),headers:{get:()=>50}});
''' + js[selection_start:selection_end] + js[timeline_start:timeline_end] + '''
(async()=>{
await timelineTick();
assert.equal(webClockSample.paused,false);
const s={duration_seconds:100,progress:.02,karaoke_offset_seconds:.25,paused:false,playing:true,position_seconds:1},clockReceivedAt=1000,clockAdvance=0;
''' + js[metadata_start:metadata_end] + '''
assert.equal(webClockSample.duration,100);
assert.equal(webClockSample.karaokeOffset,.25);
assert.equal(webClockSample.position,2);
assert.equal(webClockSample.paused,false);
// Pre-sent frames remain available through a short network interruption.
spectrumTimeline={source:'track',position:0,at:1000,playing:true,speed:1,fps:1,width:1,start_frame:0,raw:new Uint8Array([0,20,40,60])};
assert.deepEqual([...timelineSpectrumAt(3000)],[40]);
assert.equal(timelineSpectrumAt(6000).length,0);
answer.playing=false;await timelineTick();assert.equal(webClockSample.paused,true);
answer.source='stopped';await timelineTick();assert.equal(webClockSample.playing,false);
console.log('browser delivery assertions passed');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        result = subprocess.run(['node'], input=code, text=True, encoding='utf-8', capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
