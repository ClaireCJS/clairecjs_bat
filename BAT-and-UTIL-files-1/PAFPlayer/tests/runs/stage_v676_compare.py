from pathlib import Path
root=Path(__file__).resolve().parents[2]
def once(s,a,b):assert s.count(a)==1,(a[:110],s.count(a));return s.replace(a,b,1)
s=(root/'src/PAFPlayer_voice_models.py').read_text(encoding='utf8')
s=once(s,'def synthesize(model, text, gender, output, root=None):','def synthesize(model, text, gender, output, root=None, progress=None):')
s=once(s,"run_command([exe, '-m', voice, '-f', output, '--', text], timeout=300)","run_command([exe, '-m', voice, '-f', output, '--', text], timeout=300, progress=progress)")
s=once(s,"cwd=info, timeout=900)","cwd=info, timeout=900, progress=progress)")
s=once(s,"cwd=info, timeout=1800)","cwd=info, timeout=1800, progress=progress)")
s=once(s,"    results = []\n    for model in models:","    results = [];completed=0;total=len(models)*len(SAMPLES)\n    for model in models:")
s=once(s,"            results.append({'model':model, 'status':'not installed'}); continue", "            results.append({'model':model, 'status':'not installed'});progress(CATALOG[model]['name']+' is not installed');completed+=len(SAMPLES)\n            if hasattr(progress,'overall'):progress.overall(completed,total,'samples')\n            continue")
s=once(s,"data=synthesize(model,text,gender,out,root)","data=synthesize(model,text,gender,out,root,progress=progress)")
s=once(s,"                results.append({'model':model, 'gender':gender, 'status':'error', 'error':str(exc)})\n    with (folder/'results.json')", "                results.append({'model':model, 'gender':gender, 'status':'error', 'error':str(exc)})\n            completed+=1\n            if hasattr(progress,'overall'):progress.overall(completed,total,'samples')\n    with (folder/'results.json')")
s=once(s,"    choices={}; availability={}\n    for key,item in CATALOG.items():", """    choices={}; availability={};installed_state={key:bool(installed(key)) for key in CATALOG}
    select_all=tk.BooleanVar(value=all(installed_state.values()))
    def select_all_changed():
        for value in choices.values():value.set(select_all.get())
    def sync_select_all():select_all.set(all(value.get() for value in choices.values()))
    ttk.Checkbutton(frame,text='Select all / unselect all',variable=select_all,command=select_all_changed).pack(anchor='w')
    for key,item in CATALOG.items():""")
s=once(s,"row=ttk.Frame(frame);row.pack(fill='x',pady=3);value=tk.BooleanVar(value=False);choices[key]=value", "row=ttk.Frame(frame);row.pack(fill='x',pady=3);value=tk.BooleanVar(value=not installed_state[key] if not all(installed_state.values()) else True);choices[key]=value")
s=once(s,"ttk.Checkbutton(row,text=item['name'],variable=value).pack(side='left')", "ttk.Checkbutton(row,text=item['name'],variable=value,command=sync_select_all).pack(side='left')")
s=once(s,"label=ttk.Label(row,text='Installed' if installed(key) else 'Not installed')", "label=ttk.Label(row,text='Installed' if installed_state[key] else 'Not installed')")
s=once(s,"    status=tk.StringVar(value='Ready. Existing Piper voices are detected automatically.')", "    sync_select_all()\n    status=tk.StringVar(value='Ready. Uninstalled models are selected; select models to compare.')")
old="    log=tk.Text(frame,height=13,wrap='word');log.pack(fill='both',expand=True)\n    events=queue.Queue();buttons=[];activity={'started':None,'status':'Ready','last_bytes':0.0}"
new="""    notebook=ttk.Notebook(frame);notebook.pack(fill='both',expand=True)
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
"""
s=once(s,old,new)
s=once(s,"        def bytes(self,name,done,total,speed):events.put(('bytes',(name,done,total,speed)))", "        def bytes(self,name,done,total,speed):events.put(('bytes',(name,done,total,speed)))\n        def overall(self,done,total,unit):events.put(('overall',(done,total,unit)))")
s=once(s,"done,total=value;overall_bar.config(value=100*done/max(1,total));overall_label.set(f'Overall: {done}/{total} models')", "done,total,unit=value;overall_bar.config(value=100*done/max(1,total));overall_label.set(f'Overall: {done}/{total} {unit}')")
s=once(s,"                elif kind=='done':", "                elif kind=='results':\n                    display_results(*value)\n                elif kind=='done':")
s=once(s,"    def run(task):\n        selected=", "    def run(task,action):\n        selected=")
s=once(s,"        activity['started']=time.monotonic();overall_bar.config(value=0);overall_label.set('Overall: 0/'+str(len(selected))+' models')", "        activity['started']=time.monotonic();activity['status']=action+'…';status.set(activity['status']);notebook.select(progress_tab);log.insert('end',activity['status']+'\\n');log.see('end');current_bar.config(mode='indeterminate');current_bar.start(12);overall_bar.config(value=0);overall_label.set('Overall: starting')")
s=once(s,"events.put(('overall',(index+1,len(selected))))", "events.put(('overall',(index+1,len(selected),'models')))")
s=once(s,"        folder,results=compare(selected,progress)","        folder,results=compare(selected,reporter)")
s=once(s,"        events.put(('overall',(len(selected),len(selected))))\n        if os.name=='nt':os.startfile(folder)\n        return sum(row['status']!='ok' for row in results)","        events.put(('results',(folder,results)))\n        return sum(row['status']!='ok' for row in results)")
s=once(s,"for label,callback in [('Download selected',lambda:run(do_install)),('Compare selected',lambda:run(do_compare))]:", "for label,callback in [('Download selected',lambda:run(do_install,'Downloading selected models')),('Compare selected',lambda:run(do_compare,'Comparing selected models'))]:")
s=once(s,"    ttk.Button(action_bar,text='Close',command=window.destroy).pack(side='right')", "    ttk.Button(action_bar,text='Close',command=window.destroy).pack(side='right')\n    result_button=ttk.Button(action_bar,text='Open results',command=open_results,state='disabled');result_button.pack(side='left',padx=(0,8))")
compile(s,'voice candidate','exec');dest=root/'tests/runs/PAFPlayer_voice_models_v676_candidate.py'
with dest.open('x',encoding='utf8',newline='') as f:f.write(s)
print('Staged selection, scrollable progress and playable comparison results.')
