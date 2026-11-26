import ast
import inspect
import threading
import unittest
from unittest.mock import Mock, patch

import PAFPlayer as app

class SimpleInterruptTests(unittest.TestCase):
    def payload(self, simple, ctrl_break):
        stream=Mock();stream.fileno.return_value=123;stream.isatty.return_value=True
        with patch.object(app,'_SIMPLE_INLINE_CONSOLE',simple), patch.object(app.sys,'stdout',stream), patch.object(app.os,'write') as write, patch.object(app,'set_console_cursor_visible') as cursor:
            app.restore_terminal_after_interrupt(ctrl_break=ctrl_break)
        cursor.assert_called_once_with(True)
        return b''.join(call.args[1] for call in write.call_args_list)

    def test_simple_ctrl_c_and_ctrl_break_preserve_terminal_content(self):
        for ctrl_break in (False,True):
            output=self.payload(True,ctrl_break)
            self.assertIn(b'\x1b[?25h',output)
            for forbidden in (b'\x1b[H',b'\x1b[J',b'\x1b[2J',b'\x1bc',b'\x1b]112',b'\x1b[?1049'):
                self.assertNotIn(forbidden,output)

    def test_normal_ctrl_break_keeps_existing_emergency_erase(self):
        self.assertIn(b'\x1b[H\x1b[J',self.payload(False,True))

    def test_simple_signal_stops_decoder_and_unwinds_for_cleanup(self):
        tree=ast.parse(inspect.getsource(app.play_audio_file))
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='request_abort')
        environment={'simple_mode':True,'process':object(),'abort_requested':threading.Event(),
            'restore_terminal_after_interrupt':Mock(),'hard_stop_process':Mock(),'fast_console_abort':Mock(),'set_post_playback_output':Mock()}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-playback-signal-handler>','exec'),environment)
        with self.assertRaises(KeyboardInterrupt):environment['request_abort'](2,None)
        environment['restore_terminal_after_interrupt'].assert_called_once_with()
        environment['hard_stop_process'].assert_called_once_with(environment['process'],wait=False)
        environment['fast_console_abort'].assert_not_called()
        self.assertTrue(environment['abort_requested'].is_set())

    def test_normal_signal_keeps_fast_abort(self):
        tree=ast.parse(inspect.getsource(app.play_audio_file))
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='request_abort')
        environment={'simple_mode':False,'process':object(),'abort_requested':threading.Event(),
            'restore_terminal_after_interrupt':Mock(),'hard_stop_process':Mock(),'fast_console_abort':Mock(),'set_post_playback_output':Mock()}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-playback-signal-handler>','exec'),environment)
        environment['request_abort'](2,None)
        environment['fast_console_abort'].assert_called_once_with(environment['process'])

    def test_startup_labels_use_actual_port_width(self):
        for port in (666,12345):
            label=f'🌐 {app.PROGRAM_TITLE} {app.PROGRAM_VERSION.casefold()} webserver OPEN on port {port}'
            web=app.format_startup_status(label,'URL')
            monkey=app.format_startup_status('💰 MonkeyMote listening','address')
            self.assertEqual(web,label+': URL')
            self.assertEqual(app.terminal_cell_width(web.split(':',1)[0]),app.terminal_cell_width(monkey.split(':',1)[0]))
