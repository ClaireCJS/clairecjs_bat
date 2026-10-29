"""ICGF's single-key review/adjustment workflow, separate from text entry."""
from dataclasses import dataclass,replace
import os
from pathlib import Path
import re
import sys
import time

from .errors import Cancelled,ICGFError,RenderBlocked,SelectionRequired
from .presentation import color,CYAN,GREEN,YELLOW


@dataclass
class Choice:
    key: str
    label: str
    reason: str = ''


def console_key():
    """Read one key, without line buffering or an ENTER requirement."""
    if os.name=='nt':
        from .console_input import read_key
        return read_key()
    # The bundle is Windows-only, but retain a working terminal fallback.
    import select,termios,tty
    if not select.select([sys.stdin],[],[],0)[0]:return None
    settings=termios.tcgetattr(sys.stdin)
    try:tty.setraw(sys.stdin.fileno());return sys.stdin.read(1)
    finally:termios.tcsetattr(sys.stdin,termios.TCSADRAIN,settings)


def menu_rows(choices,default,width=None,enabled=None):
    import shutil,math
    from .newspaper_columns import display_width,wrap_line
    width=max(12,int(width or shutil.get_terminal_size((100,40)).columns)-1)
    columns=min(4,len(choices),max(1,(width+3)//34))
    cell=max(8,(width-3*(columns-1))//columns)
    rows=math.ceil(len(choices)/columns);packed=[]
    for row in range(rows):
        cells=[]
        for column in range(columns):
            index=column*rows+row
            if index>=len(choices):cells.append([]);continue
            choice=choices[index]
            label=f'[{choice.key.upper()}] {choice.label}'+(' (unavailable)' if choice.reason else '')
            shade='\x1b[90m' if choice.reason else YELLOW if choice.key==default else CYAN
            cells.append([(part,shade) for part in wrap_line(label,cell)])
        for part_index in range(max(map(len,cells),default=0)):
            parts=[]
            for current in cells:
                text,shade=current[part_index] if part_index<len(current) else ('',CYAN)
                parts.append(color(text,shade,enabled)+' '*max(0,cell-display_width(text)))
            packed.append('   '.join(parts).rstrip())
    reasons={}
    for choice in choices:
        if choice.reason:reasons.setdefault(choice.reason,[]).append(choice.key.upper())
    for reason,keys in reasons.items():
        packed.extend(color(line,'\x1b[90m',enabled) for line in wrap_line('Unavailable '+', '.join(keys)+': '+reason,width))
    return packed


class PopupInput:
    def __init__(self,app,spec):self.app=app;self.spec=spec;self.artwork=None;self.token=None
    def poll(self):
        artwork=self.app.floating_artwork
        if artwork is not self.artwork:
            self.close();self.artwork=artwork
            if artwork is not None and hasattr(artwork,'begin_dialog'):self.token=artwork.begin_dialog(self.spec)
        if self.token is None:return None
        return self.artwork.dialog_action(self.token)
    def close(self):
        if self.artwork is not None and self.token is not None:self.artwork.end_dialog(self.token)
        self.artwork=None;self.token=None


def choose(app,title,choices,default,help_text,*,poll=None,aliases=None,escape='b'):
    from .console_input import artwork_shortcut
    from .newspaper_columns import wrap_line
    import shutil
    options={c.key:c for c in choices};aliases=aliases or {}
    if default not in options or options[default].reason:default=next((c.key for c in choices if not c.reason),'b')
    if not app.interactive:raise SelectionRequired(title,**app.context)
    app.initializing.clear();app.diagnostics('\n'+color(title,CYAN))
    for line in menu_rows(choices,default):app.diagnostics(line)
    escape_label=options[escape].label if escape in options else 'back'
    hint=f'ENTER={options[default].label} [{default.upper()}] · H=help · ESC={escape_label} · one key, no ENTER needed'
    width=max(12,shutil.get_terminal_size((100,40)).columns-1)
    for line in wrap_line(hint+' · Ctrl+A=art · Ctrl+Alt+A=front',width):app.diagnostics(color(line,YELLOW))
    mirror=PopupInput(app,{'kind':'menu','title':title,'choices':[vars(c) for c in choices],'default':default,'help':help_text}) if poll is None else None
    try:
        while True:
            if poll is not None:
                value=poll()
                if value is not None:return value
            clicked=mirror.poll() if mirror else None
            if clicked is not None:key=clicked[0]
            elif app.ask_callback is not None:
                try:key=str(app.ask_callback(title+' ('+hint+'): '))
                except EOFError as error:raise Cancelled('Input closed; current image and job retained.',**app.context) from error
            else:
                key=console_key()
                if key is None:time.sleep(.025);continue
            if artwork_shortcut(app,key):continue
            if key=='\x03':raise KeyboardInterrupt
            if key=='\x1b':key=escape
            elif key in ('','\r','\n'):key=default
            else:key=key.strip().lower()
            key=aliases.get(key,key)
            if key in ('h','?','help'):app.diagnostics(help_text+'\n'+hint);continue
            if key in options:
                if options[key].reason:
                    app.diagnostics(color('⚠️ '+options[key].label+': '+options[key].reason,YELLOW));continue
                return key
            app.diagnostics('Choose one displayed key. H explains this menu; ESC='+escape_label+'.')
    finally:
        if mirror:mirror.close()


def ask_value(app,label,current='',*,escape=False,prefilled=False):
    from .console_input import artwork_shortcut
    from .newspaper_columns import ANSI
    mirror=PopupInput(app,{'kind':'input','title':ANSI.sub('',label),'default':str(current)})
    value=str(current) if prefilled else '';fresh=prefilled
    sys.stderr.write(label+' '+(value if prefilled else ''));sys.stderr.flush()
    try:
        while True:
            clicked=mirror.poll()
            if clicked is not None:
                answer=clicked[0];sys.stderr.write('\n');sys.stderr.flush()
                return (None if escape else str(current)) if answer is None else str(answer)
            key=console_key()
            if key is None:time.sleep(.025);continue
            if artwork_shortcut(app,key):continue
            if key=='\x03':raise KeyboardInterrupt
            if key=='\x1b':sys.stderr.write('\n');return None if escape else str(current)
            if key in ('\r','\n'):sys.stderr.write('\n');return value or str(current)
            if key=='\b':
                if value:value=value[:-1];sys.stderr.write('\b \b')
                fresh=False
            elif key.isprintable():
                if fresh:
                    sys.stderr.write('\b'*len(value)+' '*len(value)+'\b'*len(value));value='';fresh=False
                value+=key;sys.stderr.write(key)
            sys.stderr.flush()
    finally:mirror.close()


def region_index(app,regions,proposal=None):
    if len(regions)==1:
        app.diagnostics('Region 1 selected automatically (the only text region).');return 0
    index=((proposal or {}).get('blocked') or {}).get('region',0)
    page=index//9
    while True:
        start=page*9;shown=regions[start:start+9]
        options=[Choice(str(i+1),f'Region {start+i+1}: {r.before!r} → {r.after!r}') for i,r in enumerate(shown)]
        if start+9<len(regions):options.append(Choice('n','Next regions'))
        if page:options.append(Choice('p','Previous regions'))
        options.append(Choice('b','Back to image review'))
        default=str(index-start+1) if start<=index<start+len(shown) else '1'
        key=choose(app,'Choose text region',options,default,'Press the digit beside a region. N/P changes pages; ESC returns without changing anything.')
        if key=='b':return None
        if key=='n':page+=1
        elif key=='p':page-=1
        else:return start+int(key)-1


def line_value(app,label,current):
    """Values are a separate prefilled editor, with immediate ESC cancellation."""
    current=str(current)
    if app.ask_callback is not None:return app.question(label+' (ESC=back): ',current)
    return ask_value(app,label+' · ENTER=keep current · ESC=back',current,escape=True,prefilled=True)


def edit_wording(text):
    from .caption_editor import edit_caption
    return edit_caption(text)


def visual(app,source,image,region,protected,proposal,remember,index):
    from . import imaging
    from .cli import adjust
    fit_blocked=bool(proposal.get('blocked') and proposal['blocked']['region']==index and
                     any(word in proposal['blocked']['reason'].casefold() for word in ('fit','placement','protected text')))
    try:style=imaging.estimate(image,region);base_size=style['size']
    except (ICGFError,OSError,ValueError):style={};base_size=None
    while True:
        current=round(base_size*region.settings.get('scale',1)) if base_size is not None else None
        small_reason=('There is no replacement text to shrink.' if not region.after else
                      'Already at the minimum font size (6 pixels); edit the wording or skip this region.' if current is not None and current<=6 else '')
        options=[Choice('s','Smaller text (5%)',small_reason),Choice('l','Larger text (5%)'),
                 Choice('w','Edit prefilled replacement wording'),Choice('p','Choose background repair'),
                 Choice('m','Move text'),Choice('t','Letter spacing'),Choice('f','Font file'),
                 Choice('c','Text color'),Choice('o','Outline'),Choice('d','Shadow'),
                 Choice('a','Erasure-mask padding'),Choice('x','Text box'),Choice('r','Rotation'),
                 Choice('u','More visual settings'),Choice('k','Skip this region'),Choice('z','Reset visual settings'),
                 Choice('b','Back to image review'),Choice('q','Cancel this job')]
        if fit_blocked:
            app.diagnostics(color('⚠️ The replacement has no safe placement inside the image/protected text boxes.\n'
                'Try smaller text or edit the prefilled wording. A background repair alone does not make more room.',YELLOW))
            default='s' if not small_reason else 'w'
        elif proposal.get('blocked') and proposal['blocked']['region']==index:
            app.diagnostics(color('⚠️ '+proposal['blocked']['reason'],YELLOW));default='p'
        else:default='b'
        app.diagnostics(color(repr(region.before),GREEN)+' ➜ '+color(repr(region.after),YELLOW))
        key=choose(app,f'Adjust region {index+1}',options,default,
            'S/L changes text size; W opens the existing wording for editing; P repairs the erased background.\n'
            'Other keys open a value field with the current setting filled in. Each successful change regenerates\n'
            'a proposal for review. K leaves this region unchanged; B/ESC returns unchanged; Q cancels the job.\n'
            'Gray choices explain why they cannot be used. Choosing an adjustment never approves the image.')
        if key=='b':return 'back'
        if key=='q':return 'cancel'
        if key=='p':
            result=background(app,source,image,region,protected,proposal,remember,index)
            if result!='back':return result
            continue
        if key=='u':
            result=advanced(app,image,region)
            if result!='back':return result
            continue
        if key=='w':
            text=edit_wording(region.after)
            if text is None:continue
            if len(text)>4096:app.diagnostics('Replacement wording is limited to 4096 characters.');continue
            region.after=text;region.skipped=not bool(text!=region.before);return 'changed'
        direct={'s':'smaller','l':'larger','k':'skip','z':'reset'}
        fields={'m':('move','Move by dx,dy pixels; example -2,0',f"{region.settings.get('dx',0)},{region.settings.get('dy',0)}"),
                't':('tracking','Spacing in pixels; negative numbers tighten letters',region.settings.get('tracking',0)),
                'f':('font','Local .ttf/.otf/.ttc font path',region.settings.get('font',style.get('font',r'C:\Windows\Fonts\arial.ttf'))),
                'c':('color','Color #RRGGBB or #RRGGBBAA','#'+''.join(f'{v:02x}' for v in region.settings.get('foreground',style.get('foreground',(255,255,255,255))))),
                'o':('outline','Outline width in pixels (0–64)',region.settings.get('outline',0)),
                'd':('shadow','Shadow dx,dy,blur; example 2,2,1',','.join(str(v) for v in (*region.settings.get('shadow',(0,0)),region.settings.get('blur',0)))),
                'a':('mask','Add/remove mask pixels; example +1 or -1',0),
                'x':('box','Text bounds x1,y1,x2,y2',','.join(str(v) for v in region.settings.get('box',region.box))),
                'r':('rotation','Rotation in degrees (-180 to 180)',region.settings.get('rotation',0))}
        command=direct.get(key)
        if command is None:
            name,label,current=fields[key];value=line_value(app,label,current)
            if value is None or value=='\x1b':continue
            command=name+' '+value
        try:adjust(region,command,image.size)
        except (ICGFError,ValueError,OSError) as error:
            app.diagnostics('Adjustment was not applied: '+str(error)+'. H explains the controls.');continue
        return 'changed'


def advanced(app,image,region):
    """Keep the existing less-common renderer controls reachable by single keys."""
    from .cli import adjust
    while True:
        choices=[Choice('p','Text opacity'),Choice('o','Outline color'),Choice('s','Shadow color'),
            Choice('l','Caption-label background color'),Choice('t','Protect another text box'),
            Choice('x','Extend erasure mask in one direction'),Choice('i','Include text effects in erasure mask'),
            Choice('e','Exclude text effects from erasure mask'),Choice('b','Back to visual adjustment')]
        key=choose(app,'More visual settings',choices,'b',
            'P changes transparency; O/S changes effect colors; L draws a caption background.\n'
            'T protects a rectangular area; X extends the erasure mask on one side.\n'
            'I/E includes or excludes source shadow/outline pixels in the erasure mask. ESC returns unchanged.')
        if key=='b':return 'back'
        cfg=region.settings
        if key in ('i','e'):
            effect=choose(app,'Which source text effect?',
                [Choice('o','Outline'),Choice('s','Shadow'),Choice('b','Back')],'o',
                'Choose the source effect that the erasure mask should include or exclude.')
            if effect=='b':continue
            command=('include' if key=='i' else 'exclude')+' '+('outline' if effect=='o' else 'shadow')
        elif key=='x':
            side=choose(app,'Which mask side?',[Choice('l','Left'),Choice('r','Right'),Choice('u','Up'),Choice('d','Down'),Choice('b','Back')],
                'r','Choose the edge to extend, then enter its padding in pixels.')
            if side=='b':continue
            direction={'l':'left','r':'right','u':'up','d':'down'}[side]
            value=line_value(app,'Extra mask pixels on this side (0–128)',cfg.get('mask_sides',{}).get(direction,0))
            if value is None or value=='\x1b':continue
            command='extend '+direction+' '+value
        else:
            fields={'p':('opacity','Text opacity (0–1)',cfg.get('opacity',1)),
                'o':('outline-color','Outline color #RRGGBB or #RRGGBBAA',cfg.get('outline_color',(0,0,0,255))),
                's':('shadow-color','Shadow color #RRGGBB or #RRGGBBAA',cfg.get('shadow_color',(0,0,0,180))),
                'l':('label','Caption-label background #RRGGBB or #RRGGBBAA',cfg.get('label',(0,0,0,255))),
                't':('protect','Protect x1,y1,x2,y2 pixels',','.join(str(v) for v in region.box))}
            name,label,current=fields[key]
            if isinstance(current,tuple):current='#'+''.join(f'{v:02x}' for v in current)
            value=line_value(app,label,current)
            if value is None or value=='\x1b':continue
            command=name+' '+value
        try:adjust(region,command,image.size)
        except (ICGFError,ValueError,OSError) as error:
            app.diagnostics('Adjustment was not applied: '+str(error)+'. H explains the controls.');continue
        return 'changed'


def background(app,source,image,region,protected,proposal,remember,index):
    from . import imaging
    methods=[('f','fill','Flat color'),('g','gradient','Gradient'),('t','telea','Telea inpainting'),
             ('n','navier','Navier inpainting'),('p','patch','Neighboring patch')]
    options=[];valid=[];counter=len(proposal['artifacts'])
    app.initializing.update('Testing background repairs separately from text fit…')
    for key,method,label in methods:
        candidate=replace(region,settings=dict(region.settings,repair=method))
        try:_,diagnostic,crops=imaging.render_region(image,candidate,protected,repair_only=True)
        except (ICGFError,OSError,ValueError) as error:
            options.append(Choice(key,label,str(error)));continue
        status='background available'
        try:
            _,complete,complete_crops=imaging.render_region(image,candidate,protected)
            crops['corrected']=complete_crops['corrected'];status+='; replacement fits'
        except RenderBlocked as error:status+='; text/layout still blocked: '+str(error)
        except (ICGFError,OSError,ValueError) as error:status+='; replacement preview failed: '+str(error)
        options.append(Choice(key,label+' — '+status));valid.append((diagnostic['repair_score'],key,method))
        for kind in ('repair','corrected'):
            if kind not in crops:continue
            counter+=1
            path=Path(source).parent/(f".icgf-{proposal['transaction']}-compare-{index+1}-{counter}-{method}-{kind}.png")
            imaging.review_crop(path,crops[kind],'comparison-'+kind,proposal['artifacts'],remember,index)
            app.preview(path,label+': '+kind,detail=True)
    app.initializing.clear()
    options.extend([Choice('b','Back without changing repair'),Choice('q','Cancel this job')])
    default=min(valid)[1] if valid else 'b'
    app.diagnostics('Default: the available background preview with the lowest boundary/artifact score.\n'
        'This is a heuristic, so inspect the preview; choosing a repair still requires final image approval.')
    key=choose(app,'Choose background repair',options,default,
        'F fills with one sampled color; G blends a gradient; T/N reconstruct pixels from surrounding pixels;\n'
        'P copies a neighboring patch. Patch needs a same-size donor inside the image that avoids protected text.\n'
        'A background can be available even when the replacement text cannot fit. That separate fit problem\n'
        'needs smaller text, a move/box adjustment or different wording. B/ESC keeps the current repair.',
        aliases={method:key for key,method,label in methods})
    if key=='b':return 'back'
    if key=='q':return 'cancel'
    region.settings['repair']=next(method for k,method,label in methods if k==key)
    return 'changed'


def route(app,action,source,image,regions,protected,proposal,remember):
    index=region_index(app,regions,proposal)
    if index is None:return 'back'
    if action in ('b','background'):
        return background(app,source,image,regions[index],protected,proposal,remember,index)
    return visual(app,source,image,regions[index],protected,proposal,remember,index)


def review(app,message,blocked):
    """Keep GUI decisions live while a console key acts immediately."""
    labels={'m':'Move/squeeze text to fit','y':'Approve','a':'Add rule','e':'Edit prefilled caption',
            'r':'Reject changes','s':'Skip image','d':'Defer image',
            'o':'Correct OCR','v':'Adjust text/image','b':'Compare background repairs',
            'i':'Ignore text change','c':'Cancel job'}
    displayed=set(re.findall(r'\[([a-z])\]',message.casefold()))
    choices=[Choice(key,label,'Rendering is blocked; adjust the proposal before approving.' if blocked and key=='y' else '')
             for key,label in labels.items() if key in displayed or key=='y']
    artwork=app.floating_artwork;token=None
    if artwork is not None and app.ask_callback is None:
        token=artwork.begin_review(blocked,app.review_rules,getattr(app,'review_notes',[]),getattr(app,'review_changes',[]),getattr(app,'review_source',None))
    def poll():
        nonlocal artwork,token
        current=app.floating_artwork
        if current is not artwork:
            if token is not None:artwork.end_review(token)
            artwork=current;token=None
            if artwork is not None:token=artwork.begin_review(blocked,app.review_rules,getattr(app,'review_notes',[]),getattr(app,'review_changes',[]),getattr(app,'review_source',None))
        if token is None:return None
        action=artwork.review_action(token)
        if action is not None:return ('artwork',action)
        # A stopped/failed popup can be reopened with Ctrl+A; console decisions
        # remain usable while it is unavailable.
        if artwork.stopped.is_set():return None
        return None
    try:
        value=choose(app,'Review image',choices,('m' if 'm' in displayed else 'v') if blocked else 's',
            'Press a displayed key once; ENTER chooses the highlighted default. Approve applies only the\n'
            'rendered proposal. ENTER tries move/squeeze for a blocked render; V opens its adjustment\n'
            'menu, where ENTER tries smaller text for a fit problem. E opens the prefilled caption editor.\n'
            'Reject/Skip leaves this image unchanged; C/ESC cancels and retains resumable progress.',
            poll=poll,escape='c',aliases={'approve':'y','reject':'r','reject changes':'r','skip':'s'})
        if isinstance(value,tuple) and value[0]=='artwork':
            if os.name=='nt':
                import msvcrt
                while msvcrt.kbhit():msvcrt.getwch()
            value=value[1]
            return 's' if isinstance(value,str) and value in ('r','reject','reject changes') else value
        return {'y':'a','a':'add_rule','e':'edit_caption','r':'s'}.get(value,value)
    finally:
        if token is not None:artwork.end_review(token)
