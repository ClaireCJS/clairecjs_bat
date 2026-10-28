"""Prefilled caption edits mapped back to the detected text geometry."""
from difflib import SequenceMatcher
from .errors import IntegrityError

def caption_regions(lines,text):
    from .imaging import Region
    if not isinstance(text,str) or len(text)>100000:raise IntegrityError('Caption is too long.')
    if not text.strip():raise IntegrityError('Keep some caption text; use Skip to leave the image unchanged.')
    before=[line['text'] for line in lines];after=text.splitlines()
    if not before:raise IntegrityError('No detected text geometry is available for this image.')
    # Retain matching lines. Reflow only edited runs when lines were added or
    # removed, preserving the original caption footprint and unaffected lines.
    replacements={}
    for kind,a,b,c,d in SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if kind=='equal':continue
        if a==b:
            anchor=max(0,a-1);replacements[anchor]=replacements.get(anchor,before[anchor])+' '+' '.join(after[c:d]);continue
        new=after[c:d]
        if b-a==len(new):
            replacements.update((a+i,t) for i,t in enumerate(new));continue
        words=' '.join(new).split();total=sum(max(1,len(t)) for t in before[a:b]);offset=0;weight=0
        for i in range(a,b):
            weight+=max(1,len(before[i]));end=len(words) if i==b-1 else round(len(words)*weight/total)
            replacements[i]=' '.join(words[offset:end]);offset=end
    regions=[];protected=[w.box for line in lines for w in line['words']]
    for i,after in sorted(replacements.items()):
        line=lines[i];words=line['words']
        if not words or line['text']==after:continue
        box=(min(w.box[0] for w in words),min(w.box[1] for w in words),max(w.box[2] for w in words),max(w.box[3] for w in words))
        regions.append(Region(line['text'],after,box,min(w.confidence for w in words),words,
            [{'rule':'manual-caption','before':line['text'],'after':after,'original_span':[0,len(line['text'])]}],
            line_index=i,ocr_span=(0,len(line['text']))))
    return regions,protected

def edit_caption(text):
    import tkinter as tk
    from tkinter import ttk
    root=tk.Tk();root.title('Edit proposed caption — current text is already filled in');root.geometry('850x600')
    root.columnconfigure(0,weight=1);root.rowconfigure(1,weight=1);result=[None]
    ttk.Label(root,text='Edit the caption below. Regenerate builds a new image for approval.').grid(row=0,column=0,padx=10,pady=8)
    editor=tk.Text(root,wrap='word',undo=True,font=('Segoe UI',13),bg='#171b22',fg='#ffff58',insertbackground='#ffff58')
    editor.insert('1.0',text);editor.grid(row=1,column=0,sticky='nsew',padx=10)
    scroll=ttk.Scrollbar(root,command=editor.yview);scroll.grid(row=1,column=1,sticky='ns');editor.configure(yscrollcommand=scroll.set)
    def save():result[0]=editor.get('1.0','end-1c');root.quit()
    ttk.Button(root,text='Regenerate from edits',command=save).grid(row=2,column=0,pady=10)
    root.protocol('WM_DELETE_WINDOW',root.quit);root.bind('<Escape>',lambda e:root.quit())
    try:editor.focus_set();root.mainloop();return result[0]
    finally:root.destroy()
