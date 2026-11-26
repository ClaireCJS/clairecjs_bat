"""Immutable, disposable startup caches for the standalone PAFPlayer."""
import hashlib
import importlib.util
import json
import marshal
import subprocess
import time
import threading
from pathlib import Path
import sys
import uuid


class AnalysisCache:
    def __init__(self, root):
        self.root = Path(root)

    def key(self, path, parameters):
        try:
            path = Path(path).resolve(); stat = path.stat()
            identity = [str(path).casefold(), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, parameters]
            return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        except (OSError, TypeError, ValueError):
            return None

    def read(self, kind, key):
        if key is None: return None
        try:
            for entry in (self.root / kind / key).glob('*.json'):
                try:
                    data = json.loads(entry.read_text(encoding='utf-8'))
                    if data.get('key') == key: return data['value']
                except (OSError, ValueError, KeyError, AttributeError): pass
        except OSError: pass
        return None

    def write(self, kind, key, value):
        if key is None: return
        try:
            directory = self.root / kind / key
            directory.mkdir(parents=True, exist_ok=True)
            # Immutable records: no replacing, truncating, or deleting old data.
            with (directory / (uuid.uuid4().hex + '.json')).open('x', encoding='utf-8') as stream:
                json.dump({'key': key, 'value': value}, stream)
        except (OSError, TypeError, ValueError): pass


def tool_signature(executable):
    try:
        tool = Path(executable).resolve(); stat = tool.stat()
        return [str(tool), stat.st_size, stat.st_mtime_ns]
    except (OSError, TypeError, ValueError): return str(executable)


def audio_worker_command(script, executable=None):
    """Reuse compiled code, preserving the real script path and worker isolation."""
    script = Path(script).resolve(); executable = executable or sys.executable
    fallback = [str(executable), '-B', '-u', str(script), '--paf-audio-worker']
    try:
        source = script.read_bytes()
        key = hashlib.sha256(importlib.util.MAGIC_NUMBER + source).hexdigest()
        directory = script.parent / 'runtime/cache/worker-code' / key
        candidate = None
        for entry in directory.glob('*.pyc'):
            with entry.open('rb') as stream:
                if stream.read(4) == importlib.util.MAGIC_NUMBER:
                    candidate = entry; break
        if candidate is None:
            directory.mkdir(parents=True, exist_ok=True)
            recent = any(time.time() - marker.stat().st_mtime < 60 for marker in directory.glob('*.pending'))
            if not recent:
                marker = directory / (uuid.uuid4().hex + '.pending')
                with marker.open('x', encoding='utf-8') as stream: stream.write(str(time.time()))
                target = directory / (uuid.uuid4().hex + '.pyc')
                builder = (
                    "import sys,marshal,importlib.util;from pathlib import Path;"
                    "p=Path(sys.argv[1]);data=p.read_bytes();"
                    "payload=importlib.util.MAGIC_NUMBER+bytes(12)+marshal.dumps(compile(data,str(p),'exec'));"
                    "target=Path(sys.argv[2]);temp=target.with_suffix('.building');"
                    "f=open(temp,'xb');f.write(payload);f.close();temp.rename(target)"
                )
                process = subprocess.Popen([str(executable), '-B', '-c', builder, str(script), str(target)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0))
                threading.Thread(target=process.wait, name='paf-code-cache-builder', daemon=True).start()
            # Cache preparation must never delay the first audible preview.
            return fallback
        bootstrap = (
            "import sys,marshal,types,runpy;from pathlib import Path;"
            "source,cached=sys.argv[1:3];sys.argv=[source,'--paf-audio-worker'];"
            "sys.path.insert(0,str(Path(source).parent));\n"
            "try:\n"
            " with open(cached,'rb') as f:f.read(16);code=marshal.load(f)\n"
            " if not isinstance(code,types.CodeType):raise ValueError('Invalid worker cache')\n"
            "except (OSError,ValueError,EOFError,TypeError):\n"
            " runpy.run_path(source,run_name='__main__')\n"
            "else:\n import __main__;g=vars(__main__);g.update(__file__=source,__package__=None);exec(code,g)\n"
        )
        return [str(executable), '-B', '-u', '-c', bootstrap, str(script), str(candidate)]
    except (OSError, ValueError, TypeError): return fallback
