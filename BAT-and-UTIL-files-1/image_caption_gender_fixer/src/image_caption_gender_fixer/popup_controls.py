"""Mirror console fields in the artwork's current side or bottom layout."""
from tkinter import ttk


class ControlPanel:
    def __init__(self,viewer,base):
        self.viewer=viewer;self.base=base;self.frame=ttk.Frame(viewer.root,padding=4)
        self.callback=None;self.buttons={};self.value=None;self.entry=None;self.help_text=''
        self.spec=None;self.heading=None;self.reasons=None;self.footer=[]

    def clear(self):
        self.callback=None;self.value=None;self.entry=None;self.buttons.clear()
        self.spec=None;self.heading=None;self.reasons=None;self.footer=[]
        for child in self.frame.winfo_children():child.destroy()
        self.frame.grid_remove();self.viewer.place_controls()

    def show(self,spec,callback):
        self.clear()
        if not spec or callback is None:return
        self.spec=spec;self.callback=callback;self.help_text=spec.get('help','')
        self.heading=ttk.Label(self.frame,text=spec.get('title','Choose an action'),font=('Segoe UI',10,'bold'))
        if spec['kind']=='input':
            self.value=self.viewer.tk.StringVar(master=self.frame,value=str(spec.get('default','')))
            self.entry=ttk.Entry(self.frame,textvariable=self.value)
            self.entry.selection_range(0,'end')
            self.entry.bind('<Return>',lambda event:self.submit(self.value.get()))
            self.entry.bind('<Escape>',lambda event:(self.submit(None),'break')[1])
            self.buttons['submit']=ttk.Button(self.frame,text='Use this value',command=lambda:self.submit(self.value.get()))
            self.buttons['cancel']=ttk.Button(self.frame,text='Back / keep current',command=lambda:self.submit(None))
        else:
            reasons=[]
            for choice in spec['choices']:
                key=choice['key'];reason=choice.get('reason','')
                text=('▶ ' if key==spec['default'] else '')+'['+key.upper()+'] '+choice['label']
                button=ttk.Button(self.frame,text=text,command=lambda key=key:self.submit(key))
                button.configure(state='disabled' if reason else 'normal');self.buttons[key]=button
                if reason:reasons.append('['+key.upper()+'] '+reason)
            self.footer=[ttk.Button(self.frame,text='Help',command=self.help),
                         ttk.Button(self.frame,text='Hide window',command=self.viewer.hide)]
            if reasons:self.reasons=ttk.Label(self.frame,text='  |  '.join(dict.fromkeys(reasons)))
        self.viewer._layout_key=None;self.viewer.place_controls();self.viewer.schedule_draw()

    def relayout(self,master,row,columns,width):
        if not self.spec:return
        columns=max(1,columns)
        self.frame.grid(in_=master,row=row,column=0,columnspan=2 if master is not self.viewer.root else 1,sticky='ew')
        for col in range(6):self.frame.columnconfigure(col,weight=int(col<columns))
        self.heading.configure(wraplength=max(140,width-24))
        self.heading.grid(row=0,column=0,columnspan=columns,sticky='w')
        if self.entry is not None:
            self.entry.grid(row=1,column=0,columnspan=columns,sticky='ew',padx=3,pady=4)
            for i,button in enumerate(self.buttons.values()):button.grid(row=2+i//columns,column=i%columns,sticky='ew',padx=2,pady=2)
            return
        import textwrap
        for i,(key,button) in enumerate(self.buttons.items()):
            choice=next(c for c in self.spec['choices'] if c['key']==key)
            label=('▶ ' if key==self.spec['default'] else '')+'['+key.upper()+'] '+choice['label']
            button.configure(text='\n'.join(textwrap.wrap(label,width=max(16,int((width-24)/columns/8)))))
            button.grid(row=1+i//columns,column=i%columns,sticky='ew',padx=2,pady=2)
        row=1+(len(self.buttons)+columns-1)//columns
        for i,button in enumerate(self.footer):button.grid(row=row+i//columns,column=i%columns,sticky='ew',padx=2,pady=2)
        if self.reasons:
            self.reasons.configure(wraplength=max(140,width-24))
            self.reasons.grid(row=row+2,column=0,columnspan=columns,sticky='w')

    def help(self):
        self.viewer.notice.configure(text=self.help_text)

    def submit(self,value):
        callback=self.callback
        if callback is None:return
        self.callback=None
        for button in self.buttons.values():button.configure(state='disabled')
        callback(value)
