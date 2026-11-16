"""Cold compact/expanded artwork-cell benchmark with exact-output comparison."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards,unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('v650-resize-benchmark-'+stamp));stage.mkdir()
with (stage/'PAFPlayer.py').open('xb') as f:f.write((ROOT/'PAFPlayer.py').read_bytes())
for k in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):os.environ[k]=str(stage)
tempfile.tempdir=str(stage);sys.path.insert(0,str(stage));sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocked=install_guards(ROOT/'tests')
import PAFPlayer as app
assert app.PROGRAM_VERSION=='V650'
app.ARTWORK_SEAM_STRATEGY=5
width=140;mode=9;layout=3;rng=random.Random(650)
grids={rows:tuple(tuple(tuple(rng.randrange(256) for c in range(3)) for x in range(width*2)) for y in range(rows*4)) for rows in (42,48)}
results=[]
for rows,grid in grids.items():
    for strength in (.1,1.0):
        result={'rows':rows,'width':width,'strength':strength}
        outputs={}
        for name in ('scalar','numpy'):
            app._VISUALIZER_ART_DETAIL_GRID_CACHE.clear();app._VISUALIZER_ART_SCALE_CACHE.clear()
            app._art_detail_quantize_drcs_cached.cache_clear();app.dense_art_drcs_char.cache_clear()
            context=mock.patch.object(app,'_visualizer_numpy',return_value=None) if name=='scalar' else mock.patch.object(app,'ARTWORK_SEAM_STRATEGY',5)
            with context:
                begin=time.perf_counter();outputs[name]=app._visualizer_art_microtiles(grid,rows,width,strength,mode,layout)
                result[name+'_cold_ms']=1000*(time.perf_counter()-begin)
        assert outputs['scalar']==outputs['numpy'],'Artwork changed'
        begin=time.perf_counter()
        for _ in range(100):assert app._visualizer_art_microtiles(grid,rows,width,strength,mode,layout) is outputs['numpy']
        result['warm_ms']=1000*(time.perf_counter()-begin)/100
        result['identical']=True;results.append(result);print(json.dumps(result),flush=True)
report=unique(ROOT/'tests/reports'/('v650-resize-benchmark-'+stamp+'.json'))
with report.open('x',encoding='utf-8') as f:json.dump({'version':app.PROGRAM_VERSION,'source_sha256':hashlib.sha256((stage/'PAFPlayer.py').read_bytes()).hexdigest(),'results':results,'blocked_writes':blocked,'stage':str(stage),'limitations':'Synthetic cold artwork conversion; not a live end-to-end FPS measurement.'},f,indent=2)
print(report)
