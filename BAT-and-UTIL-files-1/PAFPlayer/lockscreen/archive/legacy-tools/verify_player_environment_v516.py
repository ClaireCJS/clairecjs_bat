"""Check the V516 fix against the real V515 player's inherited environment."""
import datetime
import json
from pathlib import Path
import sys
import time
import urllib.request
import psutil
import PAFPlayer_lockscreen as bridge
from lockscreen_installer import WindowsBackend

root = Path(__file__).resolve().parents[1]
player = psutil.Process(int(sys.argv[1]))
environment = player.environ()
working = player.cwd()
result = {'time': datetime.datetime.now().astimezone().isoformat(), 'playerPid': player.pid,
          'inheritedEnvironmentCharacters': sum(len(k)+len(v)+2 for k,v in environment.items())}
original_run = bridge.subprocess.run
original_environment = bridge.activation_environment
bridge.activation_environment = lambda: original_environment(environment)
def traced(*args, **kwargs):
    kwargs['cwd'] = working
    kwargs.setdefault('env', original_environment(environment))
    result['childEnvironmentCharacters'] = sum(len(k)+len(v)+2 for k,v in kwargs['env'].items())
    value = original_run(*args, **kwargs)
    result['launcherReturnCode'] = value.returncode
    if value.returncode: result['launcherError'] = value.stderr[-2000:]
    return value
bridge.subprocess.run = traced
child = None
try:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:666/api/remote-tray/hello', timeout=3) as response:
        hello = json.load(response)
    result['playerVersion'] = hello['version']
    child = bridge.launch('http://127.0.0.1:666', hello['identity'])
    time.sleep(7)
    assert child.poll() is None, 'Managed publisher exited'
    result['publisherPid'] = child.pid
    result['publication'] = WindowsBackend().verify_publication(root / 'lockscreen')
    assert result['publication']['officialVerified'] and result['publication']['published']
    child.signal()
    result['shutdownCode'] = child.wait(15)
    assert result['shutdownCode'] == 0
    result['success'] = True
except Exception as error:
    result['success'] = False
    result['error'] = repr(error)
finally:
    if child: child.close()
    # Leave publication available for the running player without restarting audio.
    result['standalonePublisherPid'] = WindowsBackend().activate('')
    path = root / 'tests/reports' / ('v516-player-environment-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json')
    with path.open('x', encoding='utf-8') as stream: json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
    print(path)
raise SystemExit(0 if result['success'] else 1)
