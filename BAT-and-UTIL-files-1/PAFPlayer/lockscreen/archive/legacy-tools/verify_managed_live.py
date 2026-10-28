"""Interactive-account, GET-only managed-publisher lifecycle acceptance check."""
from pathlib import Path
import datetime
import json
import sys
import time
import urllib.request
import uuid

import PAFPlayer_lockscreen as bridge
from lockscreen_installer import WindowsBackend


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / 'tests/reports' / ('v515-managed-live-' + uuid.uuid4().hex + '.json')
    result = {'time': datetime.datetime.now().astimezone().isoformat(), 'checks': []}
    child = None
    backend = WindowsBackend()
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:666/api/remote-tray/hello', timeout=3) as response:
            hello = json.load(response)
        assert hello.get('official') is True and hello.get('identity')
        child = bridge.launch('http://127.0.0.1:666', hello['identity'])
        time.sleep(9)
        assert child.poll() is None, 'Managed launch exited: ' + str(child.returncode)
        result['checks'].append('Installed signed EXE launched headlessly and remained alive')
        result['publisher_pid'] = child.pid
        result['official_identity'] = hello['identity']
        receipt = backend.verify_publication(root / 'lockscreen')
        assert receipt.get('officialVerified') and receipt.get('published')
        result['receipt'] = receipt
        child.signal()
        assert child.wait(timeout=15) == 0
        child.close()
        result['checks'].append('Owner stop event caused graceful exit with no playback commands')
        child = bridge.launch('http://127.0.0.1:666', 'wrong-session')
        assert child.wait(timeout=15) == 4
        result['checks'].append('Different official session rejected with exit code 4')
        result['success'] = True
    except Exception as error:
        result['success'] = False
        result['error'] = repr(error)
    finally:
        if child is not None:
            child.close()
        # Current player is still V514: restore independent publication until
        # the user next starts V515, which will take over automatically.
        result['standalone_publisher_pid'] = backend.activate('')
        with path.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
        print(json.dumps(result, indent=2))
        print(path)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
