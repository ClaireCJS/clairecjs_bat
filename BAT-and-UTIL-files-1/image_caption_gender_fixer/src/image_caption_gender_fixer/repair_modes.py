"""Background-repair choices and an artwork dropdown with actual crop samples."""
import base64
import io
from dataclasses import replace

from .errors import ICGFError

MODES=(
    ('auto','Automatic — flat color','Clean flat-color erasure; original pixels outside the text area stay unchanged'),
    ('fill','Flat color','Erase using one sampled background color'),
    ('original','Original pixels','Overlay without erasure; old lettering may remain underneath'),
    ('gradient','Gradient blend','Blend between the colors at the crop edges'),
    ('telea','Soft inpainting','Rebuild pixels from nearby colors'),
    ('navier','Structure inpainting','Extend nearby edges and structures'),
    ('patch','Neighboring patch','Copy a nearby matching area'),
)
KEYS={key for key,_,_ in MODES}


def _png(image):
    buffer=io.BytesIO();image.save(buffer,format='PNG');return buffer.getvalue()


def thumbnail(before,after):
    from PIL import Image,ImageDraw,ImageOps
    result=Image.new('RGB',(104,42),'#252a32')
    for x,source in ((0,before),(54,after)):
        rgba=source.convert('RGBA');canvas=Image.new('RGBA',rgba.size,'#606060');canvas.alpha_composite(rgba)
        sample=ImageOps.contain(canvas.convert('RGB'),(50,40),Image.Resampling.LANCZOS)
        result.paste(sample,(x+(50-sample.width)//2,(42-sample.height)//2))
    ImageDraw.Draw(result).line((51,0,51,41),fill='#ffff58')
    return _png(result)


def samples(image,region,protected):
    """Show old/erased crops, even if replacement text currently cannot fit."""
    from . import imaging
    choices=[];preferred='fill'
    for key,label,description in MODES[1:]:
        try:
            _,diagnostic,crops=imaging.render_region(image,replace(region,settings=dict(region.settings,repair=key)),protected,repair_only=True)
            preferred='fill'
            choices.append(dict(mode=key,label=label,description=description,available=True,
                thumbnail=thumbnail(crops['original'],crops['repair']),score=diagnostic['repair_score']))
        except (ICGFError,OSError,ValueError) as error:
            choices.append(dict(mode=key,label=label,description=description,available=False,reason=str(error)))
    automatic=next((item for item in choices if item['mode']==preferred),None)
    auto=dict(mode='auto',label=MODES[0][1],description=MODES[0][2],available=bool(automatic and automatic['available']))
    if automatic:
        for key in ('thumbnail','reason'):
            if key in automatic:auto[key]=automatic[key]
    return [auto,*choices]


def _illustration(mode):
    """Fallback swatches used before real image samples are available."""
    from PIL import Image,ImageDraw
    image=Image.new('RGB',(104,42),'#293341');draw=ImageDraw.Draw(image)
    for x in range(104):
        value=40+x if mode=='gradient' else 65
        draw.line((x,0,x,41),fill=(value,min(255,value+25),min(255,value+50)))
    if mode in ('auto','telea','navier','patch'):
        for x in range(-42,104,12):draw.line((x,0,x+42,42),fill='#8aacc0',width=3 if mode=='patch' else 1)
    draw.text((8,12),'Aa',fill='#ffff99');draw.line((51,0,51,41),fill='#ffff58')
    return _png(image)


class RepairPicker:
    def __init__(self,viewer,parent):
        from tkinter import ttk
        self.viewer=viewer;self.metadata=None;self.photos=[];self.entries={};self.options={}
        self.variable=viewer.tk.StringVar(master=viewer.root,value='auto')
        self.button=ttk.Menubutton(parent,text='🩹 Repair: Automatic',width=23,compound='left')
        self.menu=viewer.tk.Menu(self.button,tearoff=False);self.button.configure(menu=self.menu)
        self.update([],False)

    def update(self,changes,active):
        metadata=next((change.get('repairs') for change in changes if change.get('repairs')),None)
        if metadata is not self.metadata or not self.entries:
            self.metadata=metadata;self.menu.delete(0,'end');self.photos.clear();self.entries.clear()
            choices=metadata['choices'] if metadata else [dict(mode=key,label=label,description=desc,available=True) for key,label,desc in MODES]
            self.options={item['mode']:item for item in choices}
            self.menu.add_command(label=('Change '+str(metadata['index']+1)+' samples: before │ repaired' if metadata else 'Background repair samples')+' · applies to all changes',state='disabled')
            self.menu.add_separator()
            for item in choices:
                blob=item.get('thumbnail') or _illustration(item['mode'])
                photo=self.viewer.tk.PhotoImage(master=self.viewer.root,data=base64.b64encode(blob));self.photos.append(photo)
                label=item['label']
                if not item['available']:label+=' — unavailable: '+item.get('reason','No safe repair')
                self.menu.add_radiobutton(label=label,image=photo,compound='left',variable=self.variable,
                    value=item['mode'],state='normal' if item['available'] else 'disabled',
                    command=lambda mode=item['mode']:self.select(mode))
                self.entries[item['mode']]=self.menu.index('end')
            mode=metadata.get('mode','auto') if metadata else 'auto';self.variable.set(mode)
            self.button.configure(text='🩹 Repair: '+next((label for key,label,_ in MODES if key==mode),'Automatic'))
        self.button.configure(state='normal' if active and changes else 'disabled')

    def select(self,mode):
        viewer=self.viewer;option=self.options.get(mode)
        if self.button.instate(['disabled']) or not option or not option['available']:return
        payload={'action':'repair_mode','mode':mode,'source':viewer._review_source}
        if viewer._dirty:payload['text']=viewer.proposed_caption.get('1.0','end-1c')
        self.variable.set(mode);viewer.emit(payload)

    def close(self):
        self.menu.unpost();self.menu.destroy();self.button.destroy();self.photos.clear();self.metadata=None
        self.options.clear();self.entries.clear();self.variable=None;self.menu=None;self.button=None;self.viewer=None
