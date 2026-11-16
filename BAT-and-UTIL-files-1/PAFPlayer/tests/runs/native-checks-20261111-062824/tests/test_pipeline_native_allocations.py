"""Native polling retains definitions, never snapshots or COM resources."""
import ast
import ctypes
import inspect
import os
from types import SimpleNamespace as NS
import unittest
from unittest import mock

import PAFPlayer as app
import PAFPlayer_steam as steam


@unittest.skipUnless(os.name == 'nt', 'Windows native binding regression')
class NativeAllocationTests(unittest.TestCase):
    def test_diagnostic_reads_stop_growing_ctypes_type_cache(self):
        app.paf_runtime_diagnostics_snapshot()
        initial = len(ctypes._pointer_type_cache)
        for _ in range(100):
            data = app.paf_runtime_diagnostics_snapshot()
            self.assertGreater(data['memory']['working_set_bytes'], 0)
        self.assertEqual(initial, len(ctypes._pointer_type_cache))

    def test_diagnostics_read_current_values_on_every_request(self):
        kernel, api, kind = app._windows_process_memory_api()
        serial = []
        def read(handle, target, size):
            self.assertEqual(42, handle); self.assertEqual(ctypes.sizeof(kind), size)
            serial.append(1); target._obj.PrivateUsage = len(serial)
            target._obj.WorkingSetSize = len(serial)*2
            return True
        with mock.patch.object(app, '_windows_process_memory_api', return_value=(
                NS(GetCurrentProcess=lambda:42), NS(GetProcessMemoryInfo=read), kind)):
            self.assertEqual({'private_bytes':1,'working_set_bytes':2}, app.paf_runtime_diagnostics_snapshot()['memory'])
            self.assertEqual({'private_bytes':2,'working_set_bytes':4}, app.paf_runtime_diagnostics_snapshot()['memory'])

    def test_audio_binding_types_and_signatures_are_stable(self):
        original = app._external_audio_probe_api()
        before = len(ctypes._pointer_type_cache), len(ctypes._win_functype_cache)
        for _ in range(100): self.assertIs(original, app._external_audio_probe_api())
        self.assertEqual(before, (len(ctypes._pointer_type_cache), len(ctypes._win_functype_cache)))
        guid, key, kernel, user, ole = original
        self.assertEqual(16, ctypes.sizeof(guid)); self.assertEqual(20, ctypes.sizeof(key))
        self.assertIs(ole.CoCreateInstance.argtypes[0]._type_, guid)
        self.assertEqual(ctypes.sizeof(ctypes.c_void_p), ctypes.sizeof(kernel.OpenProcess.restype))

    def test_com_call_uses_original_address_without_a_pointer_self_cycle(self):
        fn = next(n for n in ast.walk(ast.parse(inspect.getsource(app.probe_external_audio_sessions)))
                  if isinstance(n, ast.FunctionDef) and n.name == 'call')
        ns = {'ct': ctypes}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), '<COM call>', 'exec'), ns)
        seen = []
        @ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_int)
        def method(this, value): seen.append((this, value)); return value+7
        table = (ctypes.c_void_p*1)(ctypes.cast(method, ctypes.c_void_p).value)
        obj = (ctypes.c_void_p*1)(ctypes.addressof(table))
        owner = ctypes.c_void_p(ctypes.addressof(obj))
        for value in range(100):
            self.assertEqual(value+7, ns['call'](owner, 0, (ctypes.c_int,), (value,)))
            self.assertIsNone(owner._objects)
        self.assertEqual([(owner.value, value) for value in range(100)], seen)

    def test_audio_probe_still_cleans_up_its_own_com_apartment_on_error(self):
        guid, key, *unused = app._external_audio_probe_api()
        for init_status in (-1, 0, 1):
            uninitialize = mock.Mock()
            ole = NS(CoInitializeEx=lambda *a:init_status, CoCreateInstance=lambda *a:-1,
                     CoUninitialize=uninitialize)
            with mock.patch.object(app, '_external_audio_probe_api', return_value=(
                    guid, key, NS(), NS(FindWindowW=lambda *a:0), ole)):
                result = app.probe_external_audio_sessions()
            self.assertFalse(result['known']); self.assertTrue(result['error'])
            self.assertEqual(0 if init_status < 0 else 1, uninitialize.call_count)

    def test_cursor_visibility_uses_fresh_values_and_keeps_rename_override(self):
        kinds=[]; shown=[]
        def read(handle, target): kinds.append(type(target._obj)); return True
        def write(handle, target): shown.append(target._obj.visible); return True
        fake = NS(GetStdHandle=lambda n:1, GetConsoleCursorInfo=read, SetConsoleCursorInfo=write)
        with mock.patch.object(ctypes.windll, 'kernel32', fake), mock.patch.object(app, '_INLINE_RENAME_CURSOR_SUFFIX', ''):
            for value in (False, True, False): app.set_console_cursor_visible(value)
            with mock.patch.object(app, '_INLINE_RENAME_CURSOR_SUFFIX', 'editing'):
                app.set_console_cursor_visible(False)
        self.assertEqual([0,1,0,1], shown); self.assertEqual(1, len(set(kinds)))

    def test_idle_input_reads_each_sample_using_one_type(self):
        kinds=[]
        def read(target):
            kinds.append(type(target._obj)); target._obj.dwTime = len(kinds)*5
            return True
        with mock.patch.object(ctypes.windll, 'user32', NS(GetLastInputInfo=read)):
            self.assertEqual([5,10,15], [app.windows_last_input_tick() for _ in range(3)])
        self.assertEqual(1, len(set(kinds)))

    def test_steam_reuses_binding_types_but_closes_per_poll_handles(self):
        api, kind = steam._process_image_api()
        self.assertIs(api, steam._process_image_api()[0]); self.assertIs(kind, steam._process_image_api()[1])
        closed=[]; buffers=[]; turn=[0]
        def first(handle, pointer): pointer._obj.pid=1; pointer._obj.name='one.exe'; turn[0]=0; return True
        def next_(handle, pointer):
            turn[0]+=1; pointer._obj.pid=2; pointer._obj.name='two.exe'
            return turn[0] < 2
        def path(handle, flags, buffer, size):
            buffers.append(id(buffer)); buffer.value = 'C:\\games\\fixture.exe'
            return True
        fake=NS(CreateToolhelp32Snapshot=lambda *a:99, Process32FirstW=first,
                Process32NextW=next_, OpenProcess=lambda flags,inherit,pid:pid+10,
                QueryFullProcessImageNameW=path, CloseHandle=closed.append)
        with mock.patch.object(steam, '_process_image_api', return_value=(fake,kind)):
            rows=steam.process_images()
        self.assertEqual([1,2], [r['pid'] for r in rows]); self.assertEqual([11,12,99], closed)
        self.assertEqual(1, len(set(buffers)))

    def test_steam_closes_snapshot_and_process_on_query_error(self):
        kind=steam._process_image_api()[1];closed=[]
        fake=NS(CreateToolhelp32Snapshot=lambda *a:99, Process32FirstW=lambda *a:True,
                OpenProcess=lambda *a:11, QueryFullProcessImageNameW=mock.Mock(side_effect=OSError('fixture')),
                CloseHandle=closed.append)
        with mock.patch.object(steam, '_process_image_api', return_value=(fake,kind)):
            with self.assertRaises(OSError): steam.process_images()
        self.assertEqual([11,99], closed)


if __name__ == '__main__': unittest.main()
