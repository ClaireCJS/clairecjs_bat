import contextlib,io,unittest
from unittest.mock import patch
import PAFPlayer as app

class NormalHeightStopTests(unittest.TestCase):
    def tearDown(self): app.set_post_playback_output(False)

    def test_multiline_and_blank_rows_reset_including_prompt_row(self):
        self.assertEqual(app.normal_height_output('Done\n\nCleanup\n'),app.BIG_OFF+'Done\n'+app.BIG_OFF+'\n'+app.BIG_OFF+'Cleanup\n'+app.BIG_OFF)
        self.assertEqual(app.normal_height_output('a\r\nb\rc'),app.BIG_OFF+'a\r\n'+app.BIG_OFF+'b\r'+app.BIG_OFF+'c')

    def test_stdout_stderr_and_fragmented_prints_are_covered(self):
        stdout=io.StringIO();stderr=io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            app.set_post_playback_output(True)
            print('Stopped','now')
            print('First\nSecond',file=app.sys.stderr)
            app.set_post_playback_output(False)
        for line in stdout.getvalue().split('\n')+stderr.getvalue().split('\n'):
            if line:self.assertTrue(line.startswith(app.BIG_OFF),repr(line))
        self.assertNotIn('\x1b[2J',stdout.getvalue())

    def test_next_track_can_use_double_height_again(self):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            app.set_post_playback_output(True)
            app.set_post_playback_output(False)
            print('\x1b#3Karaoke')
        self.assertEqual(stream.getvalue(),'\x1b#3Karaoke\n')

    def test_short_stream_writes_complete_without_losing_resets(self):
        class Short:
            def __init__(self):self.text=''
            def write(self,text):self.text+=text[:2];return len(text[:2])
        target=Short();wrapped=app.PostPlaybackOutput(target)
        with patch.object(app,'_POST_PLAYBACK_OUTPUT',True):self.assertEqual(wrapped.write('a\nb'),3)
        self.assertEqual(target.text,app.BIG_OFF+'a\n'+app.BIG_OFF+'b')

    def test_console_output_is_normalized_even_when_native_path_bypasses_proxy(self):
        with patch.object(app,'_POST_PLAYBACK_OUTPUT',True),patch.object(app,'_write_console_payload') as write,patch.object(app.sys,'stdout',io.StringIO()):
            app.write_console('a\nb')
        self.assertIn(app.BIG_OFF+'a\n'+app.BIG_OFF+'b',write.call_args.args[1])
