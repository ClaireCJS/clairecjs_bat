from pathlib import Path
root=Path(__file__).resolve().parents[2]
def once(s,a,b):assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b,1)
s=(root/'src/PAFPlayer_voice_models.py').read_text(encoding='utf8')
s=once(s,'import json\n','import json\nfrom collections import deque\nimport codecs\nimport re\n')
start=s.index('def run_command(');end=s.index('\n\ndef install(',start)
stream='''def run_command(args, *, cwd=None, timeout=3600, progress=None, valid=None):
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
        line=re.sub(r'(https?://[^\\s?]+)\\?[^\\s]+',r'\\1?[redacted]',line)
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
                pieces=re.split(r'[\\r\\n]+',pending);pending=pieces.pop()
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
        output='\\n'.join(tail)
        if process.returncode:raise RuntimeError('Command failed: '+' '.join(command[:4])+'\\n'+output[-4000:])
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
'''
s=s[:start]+stream+s[end:]
s=once(s,"run_command([sys.executable, '-m', 'venv', folder/'venv'], cwd=folder)","run_command([sys.executable, '-m', 'venv', folder/'venv'], cwd=folder, progress=progress)")
s=once(s,"run_command([python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', *packages], cwd=folder)","run_command([python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', '--progress-bar', 'on', *packages], cwd=folder, progress=progress)")
old='''            with urllib.request.urlopen(KOKORO_URL + name, timeout=120) as source, (folder/name).open('xb') as output:
                while True:
                    block = source.read(1024*1024)
                    if not block: break
                    output.write(block)
            if (folder/name).stat().st_size < 10000: raise RuntimeError('Incomplete model download: '+name)'''
new='''            with urllib.request.urlopen(KOKORO_URL + name, timeout=120) as source, (folder/name).open('xb') as output:
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
            if (folder/name).stat().st_size < 10000: raise RuntimeError('Incomplete model download: '+name)'''
s=once(s,old,new)
s=once(s,"run_command([python, '-c', code, repo, folder/'model'], cwd=folder)","run_command([python, '-u', '-c', code, repo, folder/'model'], cwd=folder, progress=progress)")
anchor="    choices={}; availability={}\n"
progressui='''    meter_row=ttk.Frame(frame);meter_row.pack(fill='x',pady=(0,4))
    current_box=ttk.Frame(meter_row);current_box.pack(side='left',fill='x',expand=True,padx=(0,8))
    ttk.Label(current_box,text='Current step').pack(anchor='w')
    current_bar=ttk.Progressbar(current_box,mode='determinate',maximum=100);current_bar.pack(fill='x')
    overall_box=ttk.Frame(meter_row);overall_box.pack(side='left',fill='x',expand=True)
    overall_label=tk.StringVar(value='Overall')
    ttk.Label(overall_box,textvariable=overall_label).pack(anchor='w')
    overall_bar=ttk.Progressbar(overall_box,mode='determinate',maximum=100);overall_bar.pack(fill='x')
'''+anchor
s=once(s,anchor,progressui)
start=s.index('    events=queue.Queue();buttons=[]');end=s.index('    def do_compare(selected):',start)
newblock='''    events=queue.Queue();buttons=[];activity={'started':None,'status':'Ready','last_bytes':0.0}
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
                    activity['status']=value;log.insert('end',value+'\\n');log.see('end')
                    current_bar.stop();current_bar.config(mode='indeterminate');current_bar.start(12)
                elif kind=='output':
                    log.insert('end',value+'\\n');log.see('end')
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
'''
s=s[:start]+newblock+s[end:]
compile(s,'voice candidate','exec');p=root/'tests/runs/PAFPlayer_voice_models_v675_candidate.py'
with p.open('x',encoding='utf8',newline='') as f:f.write(s)
print('Staged streaming model progress and progress bars.')
