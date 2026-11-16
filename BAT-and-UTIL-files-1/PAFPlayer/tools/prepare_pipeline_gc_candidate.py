"""Stage a narrowly scoped native-poll allocation fix without editing active playback."""
import ast
from datetime import datetime
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from prepare_v642_artwork_chrome import unique

def replace_function(source, name, transform):
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(True)
    old = ''.join(lines[node.lineno-1:node.end_lineno])
    return ''.join(lines[:node.lineno-1]) + transform(old) + ''.join(lines[node.end_lineno:])

def edit_main(source):
    def audio(old):
        start = old.index('    class Guid(ct.Structure):')
        end = old.index('    def guid(value):', start)
        type_block = old[start:end]
        start = old.index('    kernel = ct.WinDLL(')
        end = old.index('    names = {}', start)
        kernel_block = old[start:end]
        start = old.index('    user = ct.WinDLL(')
        end = old.index('    window = user.FindWindowW(', start)
        user_block = old[start:end]
        start = old.index('    ole = ct.OleDLL(')
        end = old.index('    def device_id(', start)
        ole_block = old[start:end]
        property_block = '''    class PropertyKey(ct.Structure):
        _fields_ = [("fmtid", Guid), ("pid", wt.DWORD)]

'''
        helper = '''@lru_cache(maxsize=1)
def _external_audio_probe_api():
    """Reuse native types/bindings; ctypes retains pointer/signature types forever.

    Only definitions are shared. COM interfaces, handles, values and apartment
    initialization still belong to each polling thread and are released there.
    """
    import ctypes as ct
    from ctypes import wintypes as wt

''' + type_block + property_block + kernel_block + user_block + ole_block + '''    return Guid, PropertyKey, kernel, user, ole


'''
        for block in (kernel_block, user_block, ole_block):
            assert old.count(block) == 1
            old = old.replace(block, '', 1)
        old = old.replace(type_block, '    Guid, PropertyKey, kernel, user, ole = _external_audio_probe_api()\n\n', 1)
        old = old.replace('''            class PropertyKey(ct.Structure):
                _fields_ = [("fmtid", Guid), ("pid", wt.DWORD)]
''', '', 1)
        old = old.replace('table = ct.cast(ptr, ct.POINTER(ct.POINTER(ct.c_void_p))).contents',
            '# Cast the address, not its owning c_void_p: the latter creates a\n'
            '        # self-reference in ctypes._objects for every COM call.\n'
            '        table = ct.cast(ptr.value, ct.POINTER(ct.POINTER(ct.c_void_p))).contents', 1)
        return helper + old
    source = replace_function(source, 'probe_external_audio_sessions', audio)
    def diagnostics(old):
        start = old.index('            from ctypes import wintypes')
        end = old.index('            counters = Counters()', start)
        block = old[start:end]
        helper = '''@lru_cache(maxsize=1)
def _windows_process_memory_api():
    """Create one memory-counter type and private bindings for on-demand reads."""
''' + ''.join(line[8:] if line.strip() else line for line in block.splitlines(True)) + '''    return kernel, psapi, Counters


'''
        return helper + old.replace(block, '            kernel, psapi, Counters = _windows_process_memory_api()\n', 1)
    source = replace_function(source, 'paf_runtime_diagnostics_snapshot', diagnostics)
    def stable_type(old, local_name, helper_name):
        node = next(n for n in ast.walk(ast.parse(old)) if isinstance(n, ast.ClassDef) and n.name == local_name)
        lines = old.splitlines(True)
        block = ''.join(lines[node.lineno-1:node.end_lineno])
        helper = f'''@lru_cache(maxsize=1)
def {helper_name}():
    """Reuse a native structure definition; allocate only the small value per poll."""
    from ctypes import wintypes
''' + ''.join(line[4:] if line.strip() else line for line in block.splitlines(True)) + f'''    return {local_name}


'''
        return helper + old.replace(block, f'        {local_name} = {helper_name}()\n', 1)
    source = replace_function(source, 'set_console_cursor_visible',
        lambda old: stable_type(old, 'CursorInfo', '_console_cursor_info_type'))
    source = replace_function(source, 'windows_last_input_tick',
        lambda old: stable_type(old, 'LASTINPUTINFO', '_windows_last_input_info_type'))
    return source

def edit_steam(source):
    source = source.replace('import ctypes\n', 'import ctypes\nfrom functools import lru_cache\n', 1)
    def transform(old):
        start = old.index('    class Entry(ctypes.Structure):')
        end = old.index('    snapshot = api.CreateToolhelp32Snapshot', start)
        block = old[start:end]
        helper = '''@lru_cache(maxsize=1)
def _process_image_api():
    """Stable ctypes types avoid a retained type graph on every Steam poll."""
''' + block + '''    return api, Entry


'''
        old = old.replace(block, '    api, Entry = _process_image_api()\n', 1)
        old = old.replace('        while more:\n', '        buffer = ctypes.create_unicode_buffer(32768)\n        while more:\n', 1)
        old = old.replace('                    buffer = ctypes.create_unicode_buffer(32768)\n', '', 1)
        return helper + old
    return replace_function(source, 'process_images', transform)

def bundle_replace(source, name, new):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '_PAF_BUNDLED_SOURCES':
                    for key, val in zip(node.value.keys, node.value.values):
                        if ast.literal_eval(key) == name:
                            old = ast.get_source_segment(source, val)
                            assert source.count(old) == 1
                            return source.replace(old, repr(new), 1)
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == '_PAF_BUNDLED_SOURCES' and ast.literal_eval(target.slice) == name:
                    old = ast.get_source_segment(source, node.value)
                    assert source.count(old) == 1
                    return source.replace(old, repr(new), 1)
    raise AssertionError(name)

if __name__ == '__main__':
    original = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'PAFPlayer.py'
    original_source = original.read_text(encoding='utf8')
    source = edit_main(original_source)
    steam = edit_steam((ROOT/'src/PAFPlayer_steam.py').read_text(encoding='utf8'))
    source = bundle_replace(source, 'PAFPlayer_steam', steam)
    compile(source, 'candidate', 'exec'); compile(steam, 'steam', 'exec')
    stage = unique(ROOT/'tests/runs'/('gc-candidate-'+datetime.now().strftime('%Y%m%d-%H%M%S')))
    stage.mkdir()
    for name, text in (('PAFPlayer.py', source), ('PAFPlayer_steam.py', steam)):
        with (stage/name).open('x', encoding='utf8', newline='') as f: f.write(text)
    print(stage/'PAFPlayer.py')
