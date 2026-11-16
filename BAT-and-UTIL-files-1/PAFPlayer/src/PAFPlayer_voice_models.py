"""Independent, opt-in local voice model downloads and listening comparisons."""
from __future__ import annotations
import json
from collections import deque
import codecs
import re
import os
import shutil
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
    try:
        from PAFPlayer_model_storage import preferred_root
        return preferred_root()
    except Exception:
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


def clean_terminal_output(text):
    """Remove terminal controls from subprocess output before displaying it."""
    text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', str(text))
    text=re.sub(r'\x1b\][^\x07]*(?:\x07|\x1b\\)', '', text)
    return ''.join(ch for ch in text if ch in '\t\n' or ord(ch)>=32 and ord(ch)!=127)


def console_message(message):
    try:print('PAFPlayer models: '+clean_terminal_output(message),flush=True)
    except (OSError,UnicodeError,ValueError):pass


def run_command(args, *, cwd=None, timeout=3600, progress=None, valid=None):
    """Stream output without blocking cancellation or losing the last error lines."""
    command=[str(x) for x in args]
    environment=os.environ.copy();environment['PYTHONUNBUFFERED']='1';environment['HF_HUB_DISABLE_PROGRESS_BARS']='0'
    process=subprocess.Popen(command,cwd=str(cwd) if cwd else None,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,env=environment,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    tail=deque(maxlen=80)
    def emit(line):
        line=clean_terminal_output(line).strip()
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
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        reader.join(timeout=3)
        if process.stdout is not None:process.stdout.close()


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


def synthesize(model, text, gender, output, root=None, progress=None):
    output = Path(output)
    if output.exists(): raise FileExistsError('Comparison output already exists')
    info = installed(model, root)
    if not info: raise ValueError(CATALOG[model]['name']+' is not installed')
    if model == 'piper':
        from PAFPlayer_dj import installed_piper_male
        exe, female = info
        male = installed_piper_male()
        voice = male if gender == 'male' and male else female
        run_command([exe, '-m', voice, '-f', output, '--', text], timeout=300, progress=progress)
        detail = 'Piper male voice' if voice == male else 'Piper default voice'
    elif model == 'kokoro':
        voice = 'am_adam' if gender == 'male' else 'af_heart'
        run_command([python_in(info), '-c', KOKORO_WORKER, info/'kokoro-v1.0.onnx', info/'voices-v1.0.bin', output, text, voice], cwd=info, timeout=900, progress=progress)
        detail = voice
    else:
        voice = 'Ryan' if gender == 'male' else 'Serena'
        run_command([python_in(info), '-c', QWEN_WORKER, info/'model', output, text, voice], cwd=info, timeout=1800, progress=progress)
        detail = voice
    with wave.open(str(output), 'rb') as wav:
        if wav.getnframes() <= 0: raise RuntimeError('Model produced empty audio')
        seconds = wav.getnframes()/wav.getframerate()
    return {'voice': detail, 'duration_seconds': round(seconds, 2)}


def compare(models, progress=lambda text: None, root=None):
    root = Path(root) if root is not None else support_root()
    destination = root/'comparisons'; destination.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='comparison-', dir=str(destination)))
    results = [];completed=0;total=len(models)*len(SAMPLES)
    for model in models:
        if model not in CATALOG: raise ValueError('Unknown voice model')
        if not installed(model, root):
            results.append({'model':model, 'status':'not installed'});progress(CATALOG[model]['name']+' is not installed');completed+=len(SAMPLES)
            if hasattr(progress,'overall'):progress.overall(completed,total,'samples')
            continue
        for gender, text in SAMPLES:
            progress('Testing '+CATALOG[model]['name']+' / '+gender)
            out = folder/(model+'-'+gender+'.wav'); started=time.monotonic()
            try:
                data=synthesize(model,text,gender,out,root,progress=progress)
                results.append({'model':model, 'gender':gender, 'status':'ok', 'file':str(out), 'generation_seconds':round(time.monotonic()-started,2), **data})
            except Exception as exc:
                results.append({'model':model, 'gender':gender, 'status':'error', 'error':str(exc)})
            completed+=1
            if hasattr(progress,'overall'):progress.overall(completed,total,'samples')
    with (folder/'results.json').open('x',encoding='utf8') as out: json.dump(results,out,indent=2,ensure_ascii=False)
    return folder,results


TEXT_MODELS = {
    'gpt-oss-hosted': 'OpenAI GPT-OSS 120B — OpenRouter free',
    'openrouter-free': 'OpenRouter free router',
    'gemini': 'Gemini — select only if project billing is disabled',
    'gpt-oss-local': 'OpenAI GPT-OSS 120B — local Ollama',
}
TEXT_EXAMPLE = {'new_tracks_since_last_dj': [{'artist':'Example Band','title':'Midnight Train','lyrics':'Lights on the water, we travel through the night.'}, {'artist':'Example Artist','title':'Sunrise','lyrics':'Morning arrives and the city wakes.'}], 'recent_tracks': [], 'recent_dialogues': []}


def local_ollama_executable():
    local=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData'/'Local')))/'Programs'/'Ollama'/'ollama.exe'
    if local.is_file():return str(local)
    return shutil.which('ollama')


def install_text_model(progress=lambda text:None):
    exe=local_ollama_executable()
    if not exe:raise RuntimeError('Install and start Ollama first, then try again. The local model needs about 65 GB of disk space.')
    progress('Downloading GPT-OSS 120B with Ollama (about 65 GB); this can take a long time.')
    run_command([exe,'pull','gpt-oss:120b'],timeout=86400,progress=progress)
    progress('GPT-OSS 120B downloaded to Ollama’s model directory.')


def compare_text(models, prompt, context, progress=lambda text: None):
    """Use one prompt and input for every explicitly selected, free text provider."""
    from PAFPlayer_dj import provider_key, _chat_dialogue, _gemini_dialogue, post_json, parse_dialogue
    if not prompt.strip():raise ValueError('Enter a prompt before comparing')
    try:parsed=json.loads(context)
    except ValueError as exc:raise ValueError('Example track data must be valid JSON') from exc
    data=json.dumps(parsed,ensure_ascii=False);results=[]
    for index,model in enumerate(models):
        if model not in TEXT_MODELS:raise ValueError('Unknown text model')
        started=time.monotonic();progress('Generating with '+TEXT_MODELS[model])
        try:
            if model in ('gpt-oss-hosted','openrouter-free'):
                key=provider_key('OPENROUTER_API_KEY')
                if not key:raise ValueError('OpenRouter API key is not configured')
                name='openai/gpt-oss-120b:free' if model=='gpt-oss-hosted' else 'openrouter/free'
                lines=_chat_dialogue('https://openrouter.ai/api/v1/chat/completions',key,name,prompt,data,2)
            elif model=='gemini':
                key=provider_key('GEMINI_API_KEY') or provider_key('GOOGLE_API_KEY')
                if not key:raise ValueError('Gemini API key is not configured')
                lines=_gemini_dialogue(key,prompt,data,2)
            else:
                value=post_json('http://127.0.0.1:11434/api/chat',{'model':'gpt-oss:120b','stream':False,'options':{'num_ctx':4096},'messages':[{'role':'system','content':prompt},{'role':'user','content':data}]},timeout=1800)
                lines=parse_dialogue(value['message']['content'],2)
            results.append({'model':model,'status':'ok','text':'\n'.join(str(speaker)+': '+line for speaker,line in lines),'seconds':round(time.monotonic()-started,1)})
        except Exception as exc:
            results.append({'model':model,'status':'error','error':str(exc),'seconds':round(time.monotonic()-started,1)})
        if hasattr(progress,'overall'):progress.overall(index+1,len(models),'models')
    return results


def launch_text_window(parent):
    import tkinter as tk
    from tkinter import ttk, messagebox
    from PAFPlayer_dj import ORIGINAL_DJ_PROMPT
    window=tk.Toplevel(parent);window.title('PAFPlayer — Compare DJ text models')
    frame=ttk.Frame(window,padding=12);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Compare DJ text models',font=('Segoe UI',14,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Every selected model gets the same prompt and example tracks. Hosted requests send that text to the provider. OpenRouter choices are free. Gemini may charge unless billing is disabled.',wraplength=850).pack(anchor='w',pady=4)
    choices={}
    for model,label in TEXT_MODELS.items():
        value=tk.BooleanVar(value=model in ('gpt-oss-hosted','openrouter-free'));choices[model]=value
        ttk.Checkbutton(frame,text=label,variable=value).pack(anchor='w')
    bar=ttk.Frame(frame);bar.pack(fill='x',pady=4)
    status=tk.StringVar(value='Ready. Local GPT-OSS 120B requires about 65 GB and substantial memory.')
    ttk.Label(frame,textvariable=status,wraplength=850).pack(anchor='w',pady=4)
    progress_bar=ttk.Progressbar(frame,mode='determinate',maximum=100);progress_bar.pack(fill='x',pady=(0,4))
    tabs=ttk.Notebook(frame);tabs.pack(fill='both',expand=True)
    prompt_frame=ttk.Frame(tabs);input_frame=ttk.Frame(tabs);output_frame=ttk.Frame(tabs)
    tabs.add(prompt_frame,text='Prompt');tabs.add(input_frame,text='Example tracks');tabs.add(output_frame,text='Progress and results')
    def text_box(container):
        box=tk.Text(container,wrap='word');scroll=ttk.Scrollbar(container,orient='vertical',command=box.yview);box.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');box.pack(side='left',fill='both',expand=True);return box
    prompt_box=text_box(prompt_frame);prompt_box.insert('1.0',ORIGINAL_DJ_PROMPT.replace('{speakers}','2').replace('{seconds}','90').replace('{women}','1').replace('{men}','1')+' Do not introduce the speakers or invent personal experiences.')
    input_box=text_box(input_frame);input_box.insert('1.0',json.dumps(TEXT_EXAMPLE,indent=2,ensure_ascii=False))
    output=text_box(output_frame);events=queue.Queue();buttons=[]
    class Reporter:
        def __init__(self):self.last_progress_time=0.0;self.last_percent=-1;self.last_console_time=0.0
        def __call__(self,value):
            value=clean_terminal_output(value);events.put(('log',value));console_message(value)
        def output(self,value):
            value=clean_terminal_output(value).strip()
            match=re.search(r'pulling\s+[0-9a-f]+:\s*(\d{1,3})%.*?(\d+(?:\.\d+)?\s*[KMGT]?B)\s*/\s*(\d+(?:\.\d+)?\s*[KMGT]?B)\s+(\d+(?:\.\d+)?\s*[KMGT]?B/s)\s+(\S+)',value,re.I)
            if match:
                percent=min(100,int(match.group(1)));now=time.monotonic()
                description=f"Downloading: {percent}% · {match.group(2)} / {match.group(3)} · {match.group(4)} · {match.group(5)} remaining"
                if percent!=self.last_percent or now-self.last_progress_time>=.5:
                    events.put(('progress',(percent,description)));self.last_progress_time=now
                if percent!=self.last_percent or now-self.last_console_time>=10:
                    console_message(description);self.last_console_time=now
                self.last_percent=percent
            elif value:
                events.put(('log',value));console_message(value)
        def overall(self,done,total,unit):
            value=f'{done}/{total} {unit} complete';events.put(('status',value));console_message(value)
    reporter=Reporter()
    def poll():
        try:
            while True:
                kind,value=events.get_nowait()
                if kind=='log':output.insert('end',value+'\n');output.see('end');status.set(value[:170])
                elif kind=='status':status.set(value)
                elif kind=='progress':
                    percent,description=value;progress_bar.config(value=percent);status.set(description)
                elif kind=='done':
                    status.set(value);console_message(value)
                    for button in buttons:button.state(['!disabled'])
        except queue.Empty:pass
        if window.winfo_exists():window.after(120,poll)
    def run(task):
        for button in buttons:button.state(['disabled'])
        tabs.select(output_frame);status.set('Starting…');progress_bar.config(value=0);output.insert('end','Starting…\n');output.see('end');console_message('Starting text model task')
        def worker():
            try:task();events.put(('done','Finished. See results above.'))
            except Exception as exc:events.put(('log','Error: '+str(exc)));events.put(('done','Stopped. See error above.'))
        threading.Thread(target=worker,daemon=True,name='paf-text-model-comparison').start()
    def start_compare():
        selected=[key for key,value in choices.items() if value.get()]
        if not selected:messagebox.showinfo('Choose a model','Select at least one text model.',parent=window);return
        prompt=prompt_box.get('1.0','end').strip();context=input_box.get('1.0','end').strip()
        def work():
            results=compare_text(selected,prompt,context,reporter)
            for row in results:
                reporter('\n━━ '+TEXT_MODELS[row['model']]+' ('+str(row['seconds'])+'s) ━━\n'+(row['text'] if row['status']=='ok' else 'Error: '+row['error']))
        run(work)
    compare_button=ttk.Button(bar,text='Compare selected text models',command=start_compare);compare_button.pack(side='left',padx=(0,8));buttons.append(compare_button)
    download_button=ttk.Button(bar,text='Download local GPT-OSS 120B (~65 GB)',command=lambda:run(lambda:install_text_model(reporter)));download_button.pack(side='left');buttons.append(download_button)
    ttk.Button(bar,text='Close',command=window.destroy).pack(side='right')
    window.update_idletasks()
    screen_width=max(320,window.winfo_screenwidth()-40);screen_height=max(240,window.winfo_screenheight()-80)
    wanted_width=min(screen_width,max(900,frame.winfo_reqwidth()+24))
    wanted_height=min(screen_height,max(760,frame.winfo_reqheight()+24))
    window.minsize(min(wanted_width,screen_width),min(wanted_height,screen_height))
    window.geometry(f'{wanted_width}x{wanted_height}')
    poll();return window


def launch_window():
    import tkinter as tk
    from tkinter import ttk, messagebox
    window=tk.Tk();window.title('PAFPlayer — Voice and text models');window.geometry('830x650')
    frame=ttk.Frame(window,padding=14);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Choose local voice models',font=('Segoe UI',15,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Select one or more models. Downloads are free but can use several GB and take time.',wraplength=780).pack(anchor='w',pady=(4,8))
    action_bar=ttk.Frame(frame);action_bar.pack(fill='x',pady=(4,8))
    storage_row=ttk.Frame(frame);storage_row.pack(fill='x',pady=(0,5))
    ttk.Label(storage_row,text='Model location:').pack(side='left')
    from PAFPlayer_model_storage import preferred_root,save_preferred_root
    storage_path=tk.StringVar(value=str(preferred_root()))
    ttk.Entry(storage_row,textvariable=storage_path).pack(side='left',fill='x',expand=True,padx=6)
    meter_row=ttk.Frame(frame);meter_row.pack(fill='x',pady=(0,4))
    current_box=ttk.Frame(meter_row);current_box.pack(side='left',fill='x',expand=True,padx=(0,8))
    ttk.Label(current_box,text='Current step').pack(anchor='w')
    current_bar=ttk.Progressbar(current_box,mode='determinate',maximum=100);current_bar.pack(fill='x')
    overall_box=ttk.Frame(meter_row);overall_box.pack(side='left',fill='x',expand=True)
    overall_label=tk.StringVar(value='Overall')
    ttk.Label(overall_box,textvariable=overall_label).pack(anchor='w')
    overall_bar=ttk.Progressbar(overall_box,mode='determinate',maximum=100);overall_bar.pack(fill='x')
    choices={}; availability={};installed_state={key:bool(installed(key)) for key in CATALOG}
    select_all=tk.BooleanVar(value=all(installed_state.values()))
    def select_all_changed():
        for value in choices.values():value.set(select_all.get())
    def sync_select_all():select_all.set(all(value.get() for value in choices.values()))
    ttk.Checkbutton(frame,text='Select all / unselect all',variable=select_all,command=select_all_changed).pack(anchor='w')
    for key,item in CATALOG.items():
        row=ttk.Frame(frame);row.pack(fill='x',pady=3);value=tk.BooleanVar(value=not installed_state[key] if not all(installed_state.values()) else True);choices[key]=value
        ttk.Checkbutton(row,text=item['name'],variable=value,command=sync_select_all).pack(side='left')
        label=ttk.Label(row,text='Installed' if installed_state[key] else 'Not installed');label.pack(side='left',padx=8);availability[key]=label
        ttk.Label(row,text=item['detail'],wraplength=500).pack(side='left',padx=10)
    sync_select_all()
    status=tk.StringVar(value='Ready. Uninstalled models are selected; select models to compare.')
    ttk.Label(frame,textvariable=status,wraplength=780).pack(anchor='w',pady=8)
    notebook=ttk.Notebook(frame);notebook.pack(fill='both',expand=True)
    progress_tab=ttk.Frame(notebook);results_tab=ttk.Frame(notebook)
    notebook.add(progress_tab,text='Progress');notebook.add(results_tab,text='Results')
    log=tk.Text(progress_tab,height=8,wrap='word');scroll=ttk.Scrollbar(progress_tab,orient='vertical',command=log.yview);log.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right',fill='y');log.pack(side='left',fill='both',expand=True)
    results_canvas=tk.Canvas(results_tab,highlightthickness=0);result_scroll=ttk.Scrollbar(results_tab,orient='vertical',command=results_canvas.yview);results_canvas.configure(yscrollcommand=result_scroll.set)
    result_scroll.pack(side='right',fill='y');results_canvas.pack(side='left',fill='both',expand=True)
    result_rows=ttk.Frame(results_canvas);results_window=results_canvas.create_window((0,0),window=result_rows,anchor='nw')
    result_rows.bind('<Configure>',lambda event:results_canvas.configure(scrollregion=results_canvas.bbox('all')))
    results_canvas.bind('<Configure>',lambda event:results_canvas.itemconfigure(results_window,width=event.width))
    result_location={'path':None};events=queue.Queue();buttons=[];activity={'started':None,'status':'Ready','last_bytes':0.0}
    def play_sample(path):
        try:
            if os.name=='nt':
                import winsound
                winsound.PlaySound(str(path),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
            else:os.startfile(path)
        except Exception as exc:messagebox.showerror('Cannot play sample',str(exc),parent=window)
    def open_results():
        if result_location['path'] and os.name=='nt':os.startfile(result_location['path'])
    def display_results(folder,rows):
        for child in result_rows.winfo_children():child.destroy()
        result_location['path']=str(folder);result_button.state(['!disabled'])
        for data in rows:
            row=ttk.Frame(result_rows);row.pack(fill='x',pady=3)
            title=CATALOG[data['model']]['name']+' · '+data.get('gender','')+' · '+data['status']
            if data.get('voice'):title+=' · '+data['voice']
            if data.get('generation_seconds') is not None:title+=f" · {data['generation_seconds']}s"
            ttk.Label(row,text=title,wraplength=520).pack(side='left',fill='x',expand=True)
            if data.get('file') and data['status']=='ok':ttk.Button(row,text='▶ Play',command=lambda file=data['file']:play_sample(file)).pack(side='right')
            elif data.get('error'):ttk.Label(row,text=data['error'][:160],wraplength=250).pack(side='right')
        notebook.select(results_tab)

    class Reporter:
        def __call__(self,text):events.put(('message',str(text)));console_message(str(text))
        def output(self,text):
            text=clean_terminal_output(text);events.put(('output',text))
            if not re.search(r'(?<![0-9])(100|[0-9]{1,2})%',text):console_message(text)
        def bytes(self,name,done,total,speed):events.put(('bytes',(name,done,total,speed)))
        def overall(self,done,total,unit):events.put(('overall',(done,total,unit)))
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
                    match=re.search(r'(?<![0-9])(100|[0-9]{1,2})%',value)
                    if match:
                        current_bar.stop();current_bar.config(mode='determinate',value=int(match.group(1)))
                        activity['status']=value[:200]
                elif kind=='bytes':
                    name,done,total,speed=value
                    activity['status']=name+': '+f'{done/1048576:.1f} MiB'+(f' / {total/1048576:.1f} MiB ({100*done/total:.0f}%)' if total else '')+f' at {speed/1048576:.1f} MiB/s'
                    if total:
                        current_bar.stop();current_bar.config(mode='determinate',value=min(100,100*done/total))
                    elif str(current_bar.cget('mode'))!='indeterminate':
                        current_bar.config(mode='indeterminate');current_bar.start(12)
                elif kind=='overall':
                    done,total,unit=value;overall_bar.config(value=100*done/max(1,total));overall_label.set(f'Overall: {done}/{total} {unit}')
                elif kind=='results':
                    display_results(*value)
                elif kind=='done':
                    current_bar.stop();current_bar.config(mode='determinate',value=100 if value.startswith('Finished') else 0)
                    for button in buttons:button.state(['!disabled'])
                    for key,label in availability.items():label.config(text='Installed' if installed(key) else 'Not installed')
                    activity['status']=value;activity['started']=None
        except queue.Empty:pass
        elapsed='' if activity['started'] is None else f"  ·  {int(time.monotonic()-activity['started'])}s elapsed"
        status.set(activity['status']+elapsed)
        window.after(150,poll)
    def run(task,action,require_selection=True):
        selected=[key for key,value in choices.items() if value.get()]
        if require_selection and not selected:messagebox.showinfo('Choose a model','Select one or more models first.',parent=window);return
        for button in buttons:button.state(['disabled'])
        activity['started']=time.monotonic();activity['status']=action+'…';status.set(activity['status']);notebook.select(progress_tab);log.insert('end',activity['status']+'\n');log.see('end');current_bar.config(mode='indeterminate');current_bar.start(12);overall_bar.config(value=0);overall_label.set('Overall: starting')
        def work():
            try:
                failures=task(selected)
                events.put(('done','Finished with errors. See the results above.' if failures else 'Finished. See the results above.'))
            except Exception as exc:events.put(('message','Error: '+str(exc)));events.put(('done','Stopped; see the error above.'))
        threading.Thread(target=work,daemon=True).start()
    def progress(text):reporter(text)
    def do_install(selected):
        failures=0
        for index,model in enumerate(selected):
            try:reporter('Ready: '+str(install(model,reporter)))
            except Exception as exc:failures+=1;reporter(CATALOG[model]['name']+' failed: '+str(exc))
            events.put(('overall',(index+1,len(selected),'models')))
        return failures
    def do_compare(selected):
        folder,results=compare(selected,reporter)
        for row in results:
            progress(CATALOG[row['model']]['name']+' '+row.get('gender','')+': '+row['status']+(' — '+row.get('file','') if row['status']=='ok' else ' — '+row.get('error','')))
        progress('Comparison folder: '+str(folder))
        events.put(('results',(folder,results)))
        return sum(row['status']!='ok' for row in results)
    def browse_storage():
        from tkinter import filedialog
        path=filedialog.askdirectory(parent=window,title='Choose empty model destination',mustexist=True)
        if path:storage_path.set(path)
    def do_move(_selected):
        from PAFPlayer_model_storage import relocate
        results=relocate(storage_path.get(),reporter)
        save_preferred_root(storage_path.get())
        os.environ['PAFPLAYER_MODEL_ROOT']=str(Path(storage_path.get()).expanduser().resolve())
        for item in results:reporter(item['name']+' now uses '+item['new_path']+'; original backup: '+item['backup'])
        reporter('Saved model location for future PAFPlayer runs: '+str(preferred_root()))
        return 0
    ttk.Button(storage_row,text='Browse…',command=browse_storage).pack(side='left',padx=(0,6))
    move_button=ttk.Button(storage_row,text='Move models',command=lambda:run(do_move,'Moving and verifying model stores',False));move_button.pack(side='left');buttons.append(move_button)
    for label,callback in [('Download selected',lambda:run(do_install,'Downloading selected models')),('Compare selected',lambda:run(do_compare,'Comparing selected models'))]:
        button=ttk.Button(action_bar,text=label,command=callback);button.pack(side='left',padx=(0,8));buttons.append(button)
    ttk.Button(action_bar,text='Close',command=window.destroy).pack(side='right')
    ttk.Button(action_bar,text='Text models…',command=lambda:launch_text_window(window)).pack(side='left',padx=(0,8))
    result_button=ttk.Button(action_bar,text='Open results',command=open_results,state='disabled');result_button.pack(side='left',padx=(0,8))
    window.update_idletasks()
    screen_width=max(320,window.winfo_screenwidth()-40);screen_height=max(240,window.winfo_screenheight()-80)
    wanted_width=min(screen_width,max(830,frame.winfo_reqwidth()+28))
    wanted_height=min(screen_height,max(650,frame.winfo_reqheight()+28))
    window.minsize(min(wanted_width,screen_width),min(wanted_height,screen_height));window.geometry(f'{wanted_width}x{wanted_height}')
    console_message('Model window opened. Progress will appear here and in the window.')
    poll();window.mainloop();console_message('Model window closed.');return 0
