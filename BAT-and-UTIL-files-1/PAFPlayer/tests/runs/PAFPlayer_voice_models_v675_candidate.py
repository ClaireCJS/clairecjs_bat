"""Independent, opt-in local voice model downloads and listening comparisons."""
from __future__ import annotations
import json
from collections import deque
import codecs
import re
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import wave

CATALOG = {
    'piper': {'name': 'Piper', 'detail': 'Small, fast; about 63 MB per voice, plus dependencies.'},
    'kokoro': {'name': 'Kokoro 82M', 'detail': 'More voice choices; roughly 350 MB of model files plus dependencies.'},
    'qwen-small': {'name': 'Qwen3-TTS 0.6B', 'detail': 'Expressive; multi-gigabyte download including dependencies.'},
    'qwen-large': {'name': 'Qwen3-TTS 1.7B', 'detail': 'Larger expressive model; several GB including dependencies.'},
}
SAMPLES = (
    ('female', 'Welcome back. That last song had an unusual title, and the next one brings a completely different mood.'),
    ('male', 'I like that contrast. Let us listen to another track and see where the music takes us.'),
)
KOKORO_URL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'


def support_root():
    base = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
    return Path(base) / 'PAFPlayer' / 'support' / 'voice-models'


def python_in(folder):
    return Path(folder) / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def installed(model, root=None):
    if model == 'piper':
        from PAFPlayer_dj import installed_piper
        return installed_piper()
    root = Path(root) if root is not None else support_root()
    if model not in CATALOG: raise ValueError('Unknown voice model')
    for folder in sorted(root.glob(model + '-*'), reverse=True) if root.is_dir() else ():
        if (folder / 'complete').is_file() and python_in(folder).is_file():
            if model == 'kokoro' and not all((folder / n).is_file() for n in ('kokoro-v1.0.onnx', 'voices-v1.0.bin')): continue
            if model.startswith('qwen') and not (folder / 'model' / 'config.json').is_file(): continue
            return folder
    return None


def run_command(args, *, cwd=None, timeout=3600, progress=None, valid=None):
    """Stream output without blocking cancellation or losing the last error lines."""
    command=[str(x) for x in args]
    environment=os.environ.copy();environment['PYTHONUNBUFFERED']='1'
    process=subprocess.Popen(command,cwd=str(cwd) if cwd else None,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,env=environment,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    tail=deque(maxlen=80)
    def emit(line):
        line=line.strip()
        if not line:return
        line=re.sub(r'(https?://[^\s?]+)\?[^\s]+',r'\1?[redacted]',line)
        tail.append(line)
        if progress:
            callback=getattr(progress,'output',progress)
            callback(line)
    def read_output():
        decoder=codecs.getincrementaldecoder('utf8')(errors='replace');pending=''
        try:
            while True:
                chunk=os.read(process.stdout.fileno(),4096)
                if not chunk:break
                pending+=decoder.decode(chunk)
                pieces=re.split(r'[\r\n]+',pending);pending=pieces.pop()
                for line in pieces:emit(line)
                if len(pending)>4000:emit(pending[:4000]);pending=pending[4000:]
            pending+=decoder.decode(b'',final=True)
            if pending:emit(pending)
        except (OSError,ValueError):pass
    reader=threading.Thread(target=read_output,name='paf-model-output',daemon=True);reader.start()
    deadline=time.monotonic()+timeout
    try:
        while process.poll() is None:
            if valid is not None and not valid():
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
                raise InterruptedError('Model operation cancelled')
            if time.monotonic()>=deadline:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
                raise subprocess.TimeoutExpired(command,timeout)
            time.sleep(.1)
        reader.join(timeout=3)
        output='\n'.join(tail)
        if process.returncode:raise RuntimeError('Command failed: '+' '.join(command[:4])+'\n'+output[-4000:])
        return output
    finally:
        if process.poll() is None:process.terminate()


def report_bytes(progress, name, done, total, started):
    elapsed=max(.001,time.monotonic()-started);speed=done/elapsed
    if hasattr(progress,'bytes'):
        progress.bytes(name,done,total,speed)
    else:
        percent=f' ({done*100/total:.0f}%)' if total else ''
        progress(f'{name}: {done/1048576:.1f} MiB'+(f' / {total/1048576:.1f} MiB' if total else '')+percent)


def install(model, progress=lambda text: None, root=None):
    if model not in CATALOG: raise ValueError('Unknown voice model')
    if model == 'piper':
        from PAFPlayer_dj import ensure_piper, ensure_piper_male
        exe, voice = ensure_piper(progress, lambda: True)
        try: ensure_piper_male(exe, progress, lambda: True)
        except Exception as exc: progress('Piper is ready; second voice failed: ' + str(exc))
        return Path(exe).parent
    existing = installed(model, root)
    if existing: return existing
    root = Path(root) if root is not None else support_root()
    root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=model+'-', dir=str(root)))
    progress('Creating isolated Python environment for ' + CATALOG[model]['name'])
    run_command([sys.executable, '-m', 'venv', folder/'venv'], cwd=folder, progress=progress)
    python = python_in(folder)
    packages = ['kokoro-onnx', 'soundfile'] if model == 'kokoro' else ['qwen-tts', 'soundfile', 'huggingface_hub']
    progress('Installing dependencies (this may take several minutes)')
    run_command([python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', '--progress-bar', 'on', *packages], cwd=folder, progress=progress)
    if model == 'kokoro':
        for name in ('kokoro-v1.0.onnx', 'voices-v1.0.bin'):
            progress('Downloading ' + name)
            with urllib.request.urlopen(KOKORO_URL + name, timeout=120) as source, (folder/name).open('xb') as output:
                try: total=int(source.headers.get('Content-Length','0') or 0)
                except (AttributeError,ValueError,TypeError): total=0
                done=0;started=time.monotonic();last_report=0.0
                report_bytes(progress,name,done,total,started)
                while True:
                    block = source.read(1024*1024)
                    if not block: break
                    output.write(block);done+=len(block)
                    now=time.monotonic()
                    if now-last_report>=.2:report_bytes(progress,name,done,total,started);last_report=now
                report_bytes(progress,name,done,total,started)
            if total and done!=total:raise RuntimeError('Incomplete model download: '+name)
            if (folder/name).stat().st_size < 10000: raise RuntimeError('Incomplete model download: '+name)
    else:
        repo = 'Qwen/Qwen3-TTS-12Hz-' + ('0.6B' if model == 'qwen-small' else '1.7B') + '-CustomVoice'
        progress('Downloading ' + repo + ' (several GB)')
        code = 'from huggingface_hub import snapshot_download; import sys; snapshot_download(repo_id=sys.argv[1], local_dir=sys.argv[2])'
        run_command([python, '-u', '-c', code, repo, folder/'model'], cwd=folder, progress=progress)
        if not (folder/'model'/'config.json').is_file(): raise RuntimeError('Qwen download is incomplete')
    with (folder/'complete').open('x', encoding='utf8') as marker: marker.write(model+'\n')
    progress(CATALOG[model]['name'] + ' downloaded')
    return folder


KOKORO_WORKER = '''import sys, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro(sys.argv[1],sys.argv[2]); a,sr=k.create(sys.argv[4],voice=sys.argv[5],speed=1.0,lang="en-us");sf.write(sys.argv[3],a,sr)
'''
QWEN_WORKER = '''import sys,torch,soundfile as sf
from qwen_tts import Qwen3TTSModel
device="cuda:0" if torch.cuda.is_available() else "cpu"
model=Qwen3TTSModel.from_pretrained(sys.argv[1],device_map=device,dtype=torch.bfloat16 if device.startswith("cuda") else torch.float32,attn_implementation="eager")
audio,sr=model.generate_custom_voice(text=sys.argv[3],language="English",speaker=sys.argv[4]);sf.write(sys.argv[2],audio[0],sr)
'''


def synthesize(model, text, gender, output, root=None):
    output = Path(output)
    if output.exists(): raise FileExistsError('Comparison output already exists')
    info = installed(model, root)
    if not info: raise ValueError(CATALOG[model]['name']+' is not installed')
    if model == 'piper':
        from PAFPlayer_dj import installed_piper_male
        exe, female = info
        male = installed_piper_male()
        voice = male if gender == 'male' and male else female
        run_command([exe, '-m', voice, '-f', output, '--', text], timeout=300)
        detail = 'Piper male voice' if voice == male else 'Piper default voice'
    elif model == 'kokoro':
        voice = 'am_adam' if gender == 'male' else 'af_heart'
        run_command([python_in(info), '-c', KOKORO_WORKER, info/'kokoro-v1.0.onnx', info/'voices-v1.0.bin', output, text, voice], cwd=info, timeout=900)
        detail = voice
    else:
        voice = 'Ryan' if gender == 'male' else 'Serena'
        run_command([python_in(info), '-c', QWEN_WORKER, info/'model', output, text, voice], cwd=info, timeout=1800)
        detail = voice
    with wave.open(str(output), 'rb') as wav:
        if wav.getnframes() <= 0: raise RuntimeError('Model produced empty audio')
        seconds = wav.getnframes()/wav.getframerate()
    return {'voice': detail, 'duration_seconds': round(seconds, 2)}


def compare(models, progress=lambda text: None, root=None):
    root = Path(root) if root is not None else support_root()
    destination = root/'comparisons'; destination.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='comparison-', dir=str(destination)))
    results = []
    for model in models:
        if model not in CATALOG: raise ValueError('Unknown voice model')
        if not installed(model, root):
            results.append({'model':model, 'status':'not installed'}); continue
        for gender, text in SAMPLES:
            progress('Testing '+CATALOG[model]['name']+' / '+gender)
            out = folder/(model+'-'+gender+'.wav'); started=time.monotonic()
            try:
                data=synthesize(model,text,gender,out,root)
                results.append({'model':model, 'gender':gender, 'status':'ok', 'file':str(out), 'generation_seconds':round(time.monotonic()-started,2), **data})
            except Exception as exc:
                results.append({'model':model, 'gender':gender, 'status':'error', 'error':str(exc)})
    with (folder/'results.json').open('x',encoding='utf8') as out: json.dump(results,out,indent=2,ensure_ascii=False)
    return folder,results


def launch_window():
    import tkinter as tk
    from tkinter import ttk, messagebox
    window=tk.Tk();window.title('PAFPlayer — Local voice models');window.geometry('830x650')
    frame=ttk.Frame(window,padding=14);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Choose local voice models',font=('Segoe UI',15,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Select one or more models. Downloads are free but can use several GB and take time.',wraplength=780).pack(anchor='w',pady=(4,8))
    action_bar=ttk.Frame(frame);action_bar.pack(fill='x',pady=(4,8))
    meter_row=ttk.Frame(frame);meter_row.pack(fill='x',pady=(0,4))
    current_box=ttk.Frame(meter_row);current_box.pack(side='left',fill='x',expand=True,padx=(0,8))
    ttk.Label(current_box,text='Current step').pack(anchor='w')
    current_bar=ttk.Progressbar(current_box,mode='determinate',maximum=100);current_bar.pack(fill='x')
    overall_box=ttk.Frame(meter_row);overall_box.pack(side='left',fill='x',expand=True)
    overall_label=tk.StringVar(value='Overall')
    ttk.Label(overall_box,textvariable=overall_label).pack(anchor='w')
    overall_bar=ttk.Progressbar(overall_box,mode='determinate',maximum=100);overall_bar.pack(fill='x')
    choices={}; availability={}
    for key,item in CATALOG.items():
        row=ttk.Frame(frame);row.pack(fill='x',pady=3);value=tk.BooleanVar(value=False);choices[key]=value
        ttk.Checkbutton(row,text=item['name'],variable=value).pack(side='left')
        label=ttk.Label(row,text='Installed' if installed(key) else 'Not installed');label.pack(side='left',padx=8);availability[key]=label
        ttk.Label(row,text=item['detail'],wraplength=500).pack(side='left',padx=10)
    status=tk.StringVar(value='Ready. Existing Piper voices are detected automatically.')
    ttk.Label(frame,textvariable=status,wraplength=780).pack(anchor='w',pady=8)
    log=tk.Text(frame,height=13,wrap='word');log.pack(fill='both',expand=True)
    events=queue.Queue();buttons=[];activity={'started':None,'status':'Ready','last_bytes':0.0}
    class Reporter:
        def __call__(self,text):events.put(('message',str(text)))
        def output(self,text):events.put(('output',str(text)))
        def bytes(self,name,done,total,speed):events.put(('bytes',(name,done,total,speed)))
    reporter=Reporter()
    def poll():
        try:
            while True:
                kind,value=events.get_nowait()
                if kind=='message':
                    activity['status']=value;log.insert('end',value+'\n');log.see('end')
                    current_bar.stop();current_bar.config(mode='indeterminate');current_bar.start(12)
                elif kind=='output':
                    log.insert('end',value+'\n');log.see('end')
                elif kind=='bytes':
                    name,done,total,speed=value
                    activity['status']=name+': '+f'{done/1048576:.1f} MiB'+(f' / {total/1048576:.1f} MiB ({100*done/total:.0f}%)' if total else '')+f' at {speed/1048576:.1f} MiB/s'
                    if total:
                        current_bar.stop();current_bar.config(mode='determinate',value=min(100,100*done/total))
                    elif str(current_bar.cget('mode'))!='indeterminate':
                        current_bar.config(mode='indeterminate');current_bar.start(12)
                elif kind=='overall':
                    done,total=value;overall_bar.config(value=100*done/max(1,total));overall_label.set(f'Overall: {done}/{total} models')
                elif kind=='done':
                    current_bar.stop();current_bar.config(mode='determinate',value=100 if value.startswith('Finished') else 0)
                    for button in buttons:button.state(['!disabled'])
                    for key,label in availability.items():label.config(text='Installed' if installed(key) else 'Not installed')
                    activity['status']=value;activity['started']=None
        except queue.Empty:pass
        elapsed='' if activity['started'] is None else f"  ·  {int(time.monotonic()-activity['started'])}s elapsed"
        status.set(activity['status']+elapsed)
        window.after(150,poll)
    def run(task):
        selected=[key for key,value in choices.items() if value.get()]
        if not selected:messagebox.showinfo('Choose a model','Select one or more models first.',parent=window);return
        for button in buttons:button.state(['disabled'])
        activity['started']=time.monotonic();overall_bar.config(value=0);overall_label.set('Overall: 0/'+str(len(selected))+' models')
        def work():
            try:task(selected);events.put(('done','Finished. See the results above.'))
            except Exception as exc:events.put(('message','Error: '+str(exc)));events.put(('done','Stopped; see the error above.'))
        threading.Thread(target=work,daemon=True).start()
    def progress(text):reporter(text)
    def do_install(selected):
        for index,model in enumerate(selected):
            try:reporter('Ready: '+str(install(model,reporter)))
            except Exception as exc:reporter(CATALOG[model]['name']+' failed: '+str(exc))
            events.put(('overall',(index+1,len(selected))))
    def do_compare(selected):
        folder,results=compare(selected,progress)
        for row in results:
            progress(CATALOG[row['model']]['name']+' '+row.get('gender','')+': '+row['status']+(' — '+row.get('file','') if row['status']=='ok' else ' — '+row.get('error','')))
        progress('Comparison folder: '+str(folder))
        if os.name=='nt':os.startfile(folder)
    for label,callback in [('Download selected',lambda:run(do_install)),('Compare selected',lambda:run(do_compare))]:
        button=ttk.Button(action_bar,text=label,command=callback);button.pack(side='left',padx=(0,8));buttons.append(button)
    ttk.Button(action_bar,text='Close',command=window.destroy).pack(side='right')
    poll();window.mainloop();return 0
