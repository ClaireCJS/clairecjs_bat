"""Capture the actual launcher failure without touching playback or settings."""
import datetime
import json
from pathlib import Path
import sys
import time
import urllib.request
sys.path.insert(0, str(Path(__file__).resolve().with_name('src')))
import PAFPlayer_lockscreen as bridge

root = Path(__file__).resolve().parents[1]
result = {'time': datetime.datetime.now().astimezone().isoformat()}
original = bridge.subprocess.run
def traced(*args, **kwargs):
    value = original(*args, **kwargs)
    result['launcherReturnCode'] = value.returncode
    result['launcherStdout'] = value.stdout[-5000:]
    result['launcherStderr'] = value.stderr[-9000:]
    return value
bridge.subprocess.run = traced
child = None
try:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:666/api/remote-tray/hello', timeout=3) as response:
        hello = json.load(response)
    result['playerVersion'] = hello['version']
    result['officialIdentity'] = hello['identity']
    child = bridge.launch('http://127.0.0.1:666', hello['identity'])
    time.sleep(6)
    result['publisherPid'] = child.pid
    result['publisherExitCode'] = child.poll()
except Exception as error:
    result['error'] = repr(error)
finally:
    if child:
        child.signal()
        try: result['shutdownCode'] = child.wait(12)
        except Exception as error: result['shutdownError'] = repr(error)
        child.close()
    path = root / 'tests/reports' / ('v515-launch-diagnosis-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json')
    with path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
    print(path)
