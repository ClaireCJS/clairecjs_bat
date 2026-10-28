"""Build a real Windows GUI .scr using the installed .NET Framework compiler."""
from datetime import datetime
import hashlib
import os
from pathlib import Path
import shutil
import subprocess


def build(root=None, output=None):
    root = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[1]
    if root.is_file(): root = root.parent
    compiler = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not compiler.is_file(): raise RuntimeError('The .NET Framework 4 C# compiler is required')
    output = Path(output) if output is not None else root / 'PAFPlayer.scr'
    if output.exists():
        stem = output.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt')
        backup = output.with_name(stem + '.bak'); number = 1
        while backup.exists():
            backup = output.with_name(stem + f' ({number}).bak'); number += 1
        shutil.copyfile(output, backup)
        assert hashlib.sha256(output.read_bytes()).digest() == hashlib.sha256(backup.read_bytes()).digest()
    subprocess.run([str(compiler), '/nologo', '/target:winexe', '/platform:x64', '/optimize+',
                    '/out:' + str(output), '/reference:System.Windows.Forms.dll',
                    '/reference:System.Drawing.dll', '/reference:System.Web.Extensions.dll',
                    str(root / 'src' / 'PAFPlayer_screensaver.cs')], check=True,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if output.read_bytes()[:2] != b'MZ': raise RuntimeError('Output is not a Windows executable')
    print(str(output), hashlib.sha256(output.read_bytes()).hexdigest())
    return output


if __name__ == '__main__': build()
