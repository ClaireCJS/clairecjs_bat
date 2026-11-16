"""Compare exact color-string cache keys with dynamic full-frame artwork traffic."""
import ast
from datetime import datetime
from functools import lru_cache
import gc
import hashlib
import json
from pathlib import Path
import random
import time

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'PAFPlayer.py').read_text(encoding='utf8')
tree=ast.parse(source);ns={'lru_cache':lru_cache}
for name in ('_visualizer_packed_art_sgr','_visualizer_native_rows_output'):
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/'PAFPlayer.py'),'exec'),ns)
original=ns['_visualizer_packed_art_sgr']

@lru_cache(maxsize=16384)
def integer_cache(value):
    rgb=value.to_bytes(6,'little')
    return (f'\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]};'
            f'48;2;{rgb[3]};{rgb[4]};{rgb[5]}m')
def integer(rgb):return integer_cache(int.from_bytes(rgb,'little'))

@lru_cache(maxsize=16384)
def string_cache(rgb):
    return (f'\033[38;2;{ord(rgb[0])};{ord(rgb[1])};{ord(rgb[2])};'
            f'48;2;{ord(rgb[3])};{ord(rgb[4])};{ord(rgb[5])}m')
def string(rgb):return string_cache(rgb.decode('latin1'))

rng=random.Random(653);width=140;rows=48
fixed=[bytes(rng.randrange(256) for _ in range(6))+b'A' for _ in range(width*rows)]
frames=[]
for frame in range(200):
    pixels=b''.join(bytes(rng.randrange(256) for _ in range(6))+b'B' if (i+frame)%5==0 else color for i,color in enumerate(fixed))
    frames.append([pixels[n:n+width*7] for n in range(0,len(pixels),width*7)])
results=[];expected=None
for name,function,cache in [('bytes',original,original),('int',integer,integer_cache),('str',string,string_cache)]:
    ns['_visualizer_packed_art_sgr']=function;cache.cache_clear();gc.collect()
    before=gc.get_stats();begin=time.perf_counter();digest=hashlib.sha256()
    for packed in frames:
        output=[]
        ns['_visualizer_native_rows_output'](packed,None,False,output,True,False,False,False,False,False)
        digest.update(''.join(output).encode('ascii'))
    elapsed=time.perf_counter()-begin
    if expected is None:expected=digest.hexdigest()
    assert digest.hexdigest()==expected
    results.append({'key':name,'ms_per_frame':1000*elapsed/len(frames),
                    'collections':[a['collections']-b['collections'] for a,b in zip(gc.get_stats(),before)],
                    'cache':cache.cache_info()._asdict(),'output_sha256':expected})
name='packed-sgr-keys-'+datetime.now().strftime('%Y%m%d-%H%M%S')
p=ROOT/'tests/reports'/(name+'.json');n=0
while p.exists():n+=1;p=ROOT/'tests/reports'/(name+f' ({n}).json')
with p.open('x',encoding='utf8') as f:json.dump({'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'frames':len(frames),'results':results},f,indent=2)
print(json.dumps(results,indent=2));print(p)
