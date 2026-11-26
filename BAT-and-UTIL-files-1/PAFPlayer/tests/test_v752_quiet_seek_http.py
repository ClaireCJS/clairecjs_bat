import contextlib,io,socket,threading,unittest,urllib.request
from unittest.mock import patch
import PAFPlayer as app
from PAFPlayer_memory_audio import MemoryAudioSource

class QuietSeekHTTPTests(unittest.TestCase):
    def fail_request(self,method,error):
        source=MemoryAudioSource(b'0123456789'*100,'.flac');recorded=threading.Event();stderr=io.StringIO()
        original=source._record_http_error
        def record(exc):
            original(exc);recorded.set()
        def fail(*args,**kwargs):raise error
        try:
            with patch.object(source,'_record_http_error',side_effect=record),patch.object(app,'append_pafplayer_trace') as trace,patch.object(app,'append_pafplayer_exception') as errors,contextlib.redirect_stderr(stderr):
                with patch.object(source.server.RequestHandlerClass,method,fail):
                    with socket.create_connection(('127.0.0.1',source.server.server_port),timeout=3) as client:
                        client.sendall(('GET '+source.path+' HTTP/1.0\r\n\r\n').encode())
                        self.assertTrue(recorded.wait(3))
                self.assertEqual(stderr.getvalue(),'')
                if isinstance(error,ConnectionError):
                    trace.assert_called();errors.assert_not_called()
                else:
                    errors.assert_called_once();self.assertIs(errors.call_args.args[1],error)
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(urllib.request.Request(source.url,headers={'Range':'bytes=4-7'}),timeout=3) as response:
                self.assertEqual(response.read(),b'4567')
        finally:source.close()

    def test_aborted_header_write_is_quiet_and_logged(self):
        self.fail_request('end_headers',ConnectionAbortedError('decoder stopped while seeking'))

    def test_final_flush_reset_is_quiet_and_logged(self):
        self.fail_request('finish',ConnectionResetError('decoder restarted'))

    def test_unexpected_handler_failure_keeps_diagnostics_without_console_traceback(self):
        self.fail_request('handle_one_request',RuntimeError('unexpected test error'))

    def test_diagnostic_failure_does_not_escape_to_stderr(self):
        source=MemoryAudioSource(b'abc','.wav');stderr=io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr),patch.object(app,'append_pafplayer_trace',side_effect=OSError('log unavailable')):
                source._record_http_error(BrokenPipeError('closed decoder'))
            self.assertEqual(stderr.getvalue(),'')
            self.assertTrue(source.request_events[-1]['expected_disconnect'])
        finally:source.close()
