"""ICGF static-image adapter to PAFPlayer's current Twin DRCS artwork pipeline.

Installed ../PAFPlayer/PAFPlayer.py is authoritative. Only the dependency closure
of named graphics functions/constants is loaded; player startup never executes.
The attributed _paf_drcs_copy module is the fallback. PAFPlayer .dcc and matching
registry values are read-only: ICGF does not save/migrate any player setting.
"""
from __future__ import annotations
import ast
from functools import lru_cache
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

ROOT_NAMES=('define_all_player_drcs','_visualizer_art_microtiles','_visualizer_art_cell_styles',
            'art_detail_geometry','choose_art_detail_drcs_layout','terminal_cell_pixel_size_nonintrusive',
            'PROGRAM_VERSION','PAFPLAYER_REGISTRY_ROOT','PAFPLAYER_LEGACY_REGISTRY_ROOT')
SETTING_NAMES=('DrcsEnabled','VisualizerGranularity','DrcsArtMicrotileDetailModeV370',
               'DrcsArtBarMicrotileDetailModeV370','ArtworkSeamStrategy')


def graphics_nodes(tree):
    """Select only graphics definitions and their actual global dependencies."""
    names={}
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)): names[node.name]=node
        elif isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name): names[target.id]=node
        elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name): names[node.target.id]=node
    pending=list(ROOT_NAMES);selected=set()
    while pending:
        name=pending.pop();node=names.get(name)
        if node is None or id(node) in selected: continue
        selected.add(id(node))
        for child in ast.walk(node):
            if isinstance(child,ast.Name) and isinstance(child.ctx,ast.Load) and child.id in names:
                pending.append(child.id)
    missing=[name for name in ROOT_NAMES[:6] if name not in names]
    if missing: raise ValueError('Missing PAFPlayer DRCS graphics definitions')
    return [node for node in tree.body if id(node) in selected]


def _namespace():
    return {'__name__':'icgf_paf_twin_drcs','io':io,'json':json,'math':math,'os':os,'Path':Path,
            're':re,'shutil':shutil,'subprocess':subprocess,'threading':threading,'time':time,'lru_cache':lru_cache}


@lru_cache(maxsize=4)
def _graphics(source_text,size,mtime):
    source=Path(source_text);reason=None
    if size>=0:
        try:
            data=source.read_bytes();tree=ast.parse(data.decode('utf-8-sig'),filename=str(source))
            namespace=_namespace()
            exec(compile(ast.Module(body=graphics_nodes(tree),type_ignores=[]),str(source),'exec'),namespace)
            return namespace,{'origin':'installed-pafplayer','source':str(source),
                'source_sha256':hashlib.sha256(data).hexdigest(),'version':namespace.get('PROGRAM_VERSION')}
        except (OSError,ValueError,SyntaxError,NameError,TypeError) as error:
            reason='Installed Twin DRCS definitions unavailable: '+type(error).__name__
    else: reason='Sibling PAFPlayer source unavailable'
    from . import _paf_drcs_copy
    return vars(_paf_drcs_copy),{'origin':'internal-pafplayer-copy','source':str(Path(_paf_drcs_copy.__file__)),
        'version':getattr(_paf_drcs_copy,'PROGRAM_VERSION',None),'fallback_reason':reason}


def graphics(root):
    source=Path(root).resolve().parent/'PAFPlayer/PAFPlayer.py'
    try: info=source.stat();size=info.st_size;mtime=info.st_mtime_ns
    except OSError: size=-1;mtime=-1
    return _graphics(str(source),size,mtime)


def current_settings(root,namespace=None):
    if namespace is None: namespace,_=graphics(root)
    default=int(namespace['ART_MICROTILE_DETAIL_MODE_DEFAULT'])
    values={'DrcsEnabled':1,'VisualizerGranularity':3,'DrcsArtMicrotileDetailModeV370':default,
            'DrcsArtBarMicrotileDetailModeV370':default,'ArtworkSeamStrategy':int(namespace.get('ARTWORK_SEAM_STRATEGY',5))}
    origins={name:'PAFPlayer source default' for name in values}
    config=Path(root).resolve().parent/'PAFPlayer/PAFPlayer.dcc'
    try:
        data=json.loads(config.read_text(encoding='utf-8-sig'))
        saved=data.get('player_settings',{})
        for name in SETTING_NAMES:
            if name in saved: values[name]=int(saved[name]);origins[name]=str(config)
    except (OSError,ValueError,TypeError,AttributeError): pass
    if os.name=='nt':
        import winreg
        primary=namespace.get('PAFPLAYER_REGISTRY_ROOT',r'Software\ClaireCJS\PAFPlayer')
        legacy=namespace.get('PAFPLAYER_LEGACY_REGISTRY_ROOT',r'Software\ClaireCJS\play_audio_file')
        aliases={'DrcsArtMicrotileDetailModeV370':'MicrotileDetailMode','DrcsArtBarMicrotileDetailModeV370':'BarMicrotileDetailMode'}
        for name in SETTING_NAMES:
            for key_path,value_name in ((primary+r'\Visualizer',aliases.get(name,name)),(legacy,name)):
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key_path,0,winreg.KEY_READ) as key:
                        value,_=winreg.QueryValueEx(key,value_name)
                    values[name]=int(value);origins[name]='HKCU\\'+key_path+'\\'+value_name;break
                except (OSError,ValueError,TypeError): pass
    maximum=len(namespace['ART_MICROTILE_DETAIL_MODE_NAMES'])-1
    for name in ('DrcsArtMicrotileDetailModeV370','DrcsArtBarMicrotileDetailModeV370'):
        values[name]=min(maximum,max(0,values[name]))
    values['VisualizerGranularity']=min(3,max(1,values['VisualizerGranularity']))
    values['DrcsEnabled']=int(bool(values['DrcsEnabled']))
    values['ArtworkSeamStrategy']=min(5,max(0,values['ArtworkSeamStrategy']))
    return values,origins


def status(root):
    namespace,metadata=graphics(root);settings,origins=current_settings(root,namespace)
    mode=settings['DrcsArtMicrotileDetailModeV370']
    return {**metadata,'renderer':'pafplayer-twin-drcs','settings':settings,'setting_sources':origins,
            'detail_name':namespace['ART_MICROTILE_DETAIL_MODE_NAMES'][mode],
            'subcells':list(namespace['art_detail_geometry'](mode)),
            'bank_layout':namespace['choose_art_detail_drcs_layout'](mode,settings['DrcsArtBarMicrotileDetailModeV370'])}


def render(root,path,columns,rows):
    from PIL import Image,ImageDraw,ImageOps
    namespace,_metadata=graphics(root);settings,_=current_settings(root,namespace)
    namespace['ARTWORK_SEAM_STRATEGY']=settings['ArtworkSeamStrategy']
    mode=settings['DrcsArtMicrotileDetailModeV370'] if settings['DrcsEnabled'] else 0
    bank=namespace['choose_art_detail_drcs_layout'](mode,settings['DrcsArtBarMicrotileDetailModeV370'])
    horizontal,vertical=namespace['art_detail_geometry'](mode)
    cell_width,cell_height=namespace['terminal_cell_pixel_size_nonintrusive']()
    columns=max(1,int(columns));rows=max(1,int(rows))
    with Image.open(path) as handle: source=ImageOps.exif_transpose(handle).convert('RGBA')
    fitted=ImageOps.contain(source,(columns*cell_width,rows*cell_height),method=Image.Resampling.LANCZOS)
    columns=min(columns,max(1,math.ceil(fitted.width/cell_width)))
    rows=min(rows,max(1,math.ceil(fitted.height/cell_height)))
    canvas=Image.new('RGBA',(columns*cell_width,rows*cell_height),(224,224,224,255))
    if source.getchannel('A').getextrema()[0]<255:
        draw=ImageDraw.Draw(canvas);tile=16
        for y in range(0,canvas.height,tile):
            for x in range((y//tile%2)*tile,canvas.width,tile*2):
                draw.rectangle((x,y,x+tile-1,y+tile-1),fill=(192,192,192,255))
    canvas.alpha_composite(fitted,((canvas.width-fitted.width)//2,(canvas.height-fitted.height)//2))
    sampled=canvas.convert('RGB').resize((columns*horizontal,rows*vertical),Image.Resampling.LANCZOS)
    pixels=list(sampled.getdata());sample_width=sampled.width
    grid=tuple(tuple(pixels[y*sample_width:(y+1)*sample_width]) for y in range(sampled.height))
    if mode:
        cells=namespace['_visualizer_art_microtiles'](grid,rows,columns,1.0,mode,bank)
        styles=namespace['_visualizer_art_cell_styles'](cells,mode,columns)
        output=[namespace['define_all_player_drcs'](bank)]
    else:
        styles=tuple(tuple((rgb,rgb,f'\x1b[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m',' ',False) for rgb in row) for row in grid)
        output=[]
    for row in styles:
        output.append('\r');charset=None;previous_sgr=None
        for foreground,background,sgr,glyph,unicode_art in row:
            if unicode_art!=charset:
                output.append('\x1b(B' if unicode_art or not mode else '\x1b( @');charset=unicode_art
            if sgr!=previous_sgr: output.append(sgr);previous_sgr=sgr
            output.append(glyph)
        output.append('\x1b(B\x1b[0m\r\n')
    return ''.join(output).encode('utf-8')
