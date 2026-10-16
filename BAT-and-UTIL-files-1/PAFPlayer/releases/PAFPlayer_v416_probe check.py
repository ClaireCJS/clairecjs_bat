from pathlib import Path
import subprocess
import base64
import os
import json

code = Path(__file__).with_name('pafplayer_v416_media_probe.ps1').read_text().replace('__PAF_OWNER_PID__', str(os.getpid()))
process = subprocess.Popen(['powershell.exe', '-NoProfile', '-NonInteractive', '-MTA', '-EncodedCommand', base64.b64encode(code.encode('utf-16-le')).decode()], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
try:
    # Read-only: emit backend availability and activity counts, not media titles.
    for _ in range(2):
        snapshot = json.loads(process.stdout.readline())
        print(json.dumps({key: snapshot[key] for key in ('known', 'smtc_available', 'smtc_error', 'error', 'winamp')} | {'media_sessions': len(snapshot['media']), 'audio_sessions': len(snapshot['audio'])}))
finally:
    process.terminate()
    process.communicate(timeout=5)
