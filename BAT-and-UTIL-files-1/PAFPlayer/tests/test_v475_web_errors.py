"""Exercise the production HTTP exception boundary without starting playback."""
import ast
import contextlib
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / 'pafplayer.py'
tree = ast.parse(source.read_text(encoding='utf-8-sig'))
handler = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == 'Handler' and any(isinstance(f, ast.FunctionDef) and f.name == 'handle_one_request' for f in n.body))


class WebErrors(unittest.TestCase):
    def make_handler(self, local=True, started=False):
        records = []
        class Base:
            def handle_one_request(self):
                self._paf_response_started = started
                raise RuntimeError('fixture failure')
        namespace = dict(BaseHTTPRequestHandler=Base, contextlib=contextlib,
                         append_pafplayer_exception=lambda *args: records.append(args),
                         append_pafplayer_error=records.append)
        methods = [n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name in ('handle_one_request', 'log_error')]
        cls = ast.ClassDef(name='Handler', bases=[ast.Name(id='BaseHTTPRequestHandler', ctx=ast.Load())], keywords=[], body=methods, decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), str(source), 'exec'), namespace)
        instance = namespace['Handler']()
        instance.command='POST'; instance.path='/api/workflows/windows-media?token=secret'
        instance._client_is_local=lambda:local
        instance.responses=[]
        instance._json=lambda *args:instance.responses.append(args)
        return instance, records

    def test_local_failure_logged_and_returned(self):
        h, records = self.make_handler()
        h.handle_one_request()
        self.assertEqual(500, h.responses[0][0])
        self.assertIn('fixture failure', h.responses[0][1]['error'])
        self.assertNotIn('secret', records[0][0])
        self.assertTrue(h.close_connection)

    def test_remote_failure_does_not_expose_exception(self):
        h, records = self.make_handler(local=False)
        h.handle_one_request()
        self.assertNotIn('fixture failure', h.responses[0][1]['error'])
        self.assertEqual(1, len(records))

    def test_partial_response_is_not_followed_by_second_response(self):
        h, records = self.make_handler(started=True)
        h.handle_one_request()
        self.assertEqual([], h.responses)
        self.assertEqual(1, len(records))


if __name__ == '__main__': unittest.main()
