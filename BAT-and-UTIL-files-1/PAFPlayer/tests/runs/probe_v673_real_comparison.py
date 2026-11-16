import importlib.util,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v673_real_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as models
folder=Path(tempfile.mkdtemp(prefix='v673-real-',dir=root/'tests/runs'))
result,rows=models.compare(['piper'],root=folder)
if len(rows)!=2 or any(row['status']!='ok' for row in rows):raise SystemExit(str(rows))
print('Real Piper comparison passed:',len(rows),'WAV samples and',result/'results.json')
