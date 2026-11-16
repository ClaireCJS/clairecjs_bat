from pathlib import Path
root=Path(__file__).resolve().parents[2];src=root/'tests/runs/probe_v675_progress_window.py';dest=root/'tests/runs/probe_v675_percent_window.py';s=src.read_text(encoding='utf8')
a="progress('Downloading example');progress.output('Installer: receiving data');progress.bytes('example.bin',25,100,1048576)";b="progress('Downloading example');progress.output('Fetching files: 42%')";assert s.count(a)==1;s=s.replace(a,b,1)
a="assert float(bars[0].cget('value'))==25";b="assert float(bars[0].cget('value'))==42";assert s.count(a)==1;s=s.replace(a,b,1)
a="assert 'Installer: receiving data' in logs[0].get('1.0','end')";b="assert 'Fetching files: 42%' in logs[0].get('1.0','end')";assert s.count(a)==1;s=s.replace(a,b,1)
s=s.replace('25% current progress','42% installer-reported progress')
with dest.open('x',encoding='utf8',newline='') as f:f.write(s)
print('Created installer-percentage window probe.')
