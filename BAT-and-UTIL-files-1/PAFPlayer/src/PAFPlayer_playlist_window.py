"""Compact playlist window; player mutations are queued for its owner thread."""
from __future__ import annotations
import os
import hashlib
import shutil
from datetime import datetime
import queue
import threading
import time
from pathlib import Path


def move_row(paths, source, destination):
    """Move a single slot, preserving duplicates and every other slot's order."""
    result = list(paths)
    if not (0 <= source < len(result) and 0 <= destination < len(result)):
        raise ValueError('Playlist changed; try the drag again')
    result.insert(destination, result.pop(source))
    return result


def move_rows(paths, indices, destination):
    """Move selected slots as a group, preserving their relative order."""
    paths = list(paths)
    indices = sorted(set(indices))
    if not indices or indices[0] < 0 or indices[-1] >= len(paths) or not 0 <= destination < len(paths):
        raise ValueError('Playlist changed; try the drag again')
    if destination in indices:
        return paths, tuple(indices)
    selected = set(indices)
    block = [paths[i] for i in indices]
    remaining = [path for i, path in enumerate(paths) if i not in selected]
    before_target = sum(1 for i in range(destination) if i not in selected)
    insertion = before_target + (1 if destination > indices[0] else 0)
    return remaining[:insertion] + block + remaining[insertion:], tuple(range(insertion, insertion + len(block)))


def remap_selection(old_paths, new_paths, indices):
    """Keep duplicate occurrences distinct when a playlist snapshot changes."""
    counts = {}; keys = []
    for path in old_paths:
        counts[path] = counts.get(path, 0) + 1
        keys.append((path, counts[path]))
    wanted = {keys[i] for i in indices if 0 <= i < len(keys)}
    counts.clear(); result = []
    for i, path in enumerate(new_paths):
        counts[path] = counts.get(path, 0) + 1
        if (path, counts[path]) in wanted: result.append(i)
    return tuple(result)


def metadata_display(path):
    """Read optional tags away from Tk; retain the filename when tags are absent."""
    name = Path(path).name
    try:
        import mutagen
        media = mutagen.File(path, easy=True)
        if media is None: return name, '--:--'
        def first(key):
            value = media.get(key, []) if getattr(media, 'tags', None) else []
            return str(value[0] if isinstance(value, (tuple, list)) and value else value or '').strip()
        artist, title = first('artist'), first('title')
        label = f'{artist} - {title}' if artist and title else (title or name)
        seconds = int(media.info.length) if getattr(media, 'info', None) else -1
        return label, (f'{seconds//60}:{seconds%60:02}' if seconds >= 0 else '--:--')
    except Exception:
        return name, '--:--'


def metadata_extra(path, last_played=None):
    result={'year':'','album':'','folder':str(Path(path).parent),'genre':'','last_played':'—'}
    try:
        import mutagen
        media=mutagen.File(path,easy=True)
        for output,key in (('year','date'),('album','album'),('genre','genre')):
            values=media.get(key,[]) if media is not None and getattr(media,'tags',None) else []
            result[output]=str(values[0] if isinstance(values,(list,tuple)) and values else values or '')
    except Exception:pass
    if last_played:
        try:
            stamp=last_played(Path(path))
            result['last_played']='Loading' if stamp is None else datetime.fromtimestamp(stamp).strftime('%Y-%m-%d %I:%M %p') if stamp>0 else 'Never'
        except Exception:result['last_played']='Unavailable'
    return result


def _verified_audio_backup(path):
    path=Path(path)
    backup=path.with_name(path.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'))
    base=backup;i=0
    while True:
        try:
            with path.open('rb') as source,backup.open('xb') as target:shutil.copyfileobj(source,target,1024*1024)
            break
        except FileExistsError:
            i+=1;backup=base.with_name(base.name[:-4]+f' ({i}).bak')
    shutil.copystat(path,backup)
    def digest(file):
        h=hashlib.sha256()
        with file.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        return h.digest()
    if digest(path)!=digest(backup):raise OSError('Backup verification failed; media was not changed')
    return backup


def write_audio_tags(path, values):
    """Verify a unique sibling backup before mutating any audio metadata."""
    import mutagen
    path=Path(path);media=mutagen.File(str(path),easy=True)
    if media is None:raise ValueError('This audio format does not support editing tags')
    if media.tags is None:media.add_tags()
    backup=_verified_audio_backup(path)
    for key,value in values.items():
        if key not in ('title','artist','album','date','genre','tracknumber'):raise ValueError('Unsupported tag')
        value=str(value).strip()
        if value:media[key]=[value]
        elif key in media:del media[key]
    media.save();return backup


def read_audio_art(path):
    """Return the first embedded cover and MIME type for common tagged formats."""
    import mutagen
    from mutagen.flac import Picture
    import base64
    media=mutagen.File(str(path),easy=False)
    if media is None or media.tags is None:return None,None
    tags=media.tags
    for key,value in getattr(tags,'items',lambda:[])():
        if str(key).upper().startswith('APIC') and getattr(value,'data',None):return bytes(value.data),str(getattr(value,'mime','image/jpeg'))
    pictures=getattr(tags,'pictures',None)
    if pictures:
        picture=pictures[0];return bytes(picture.data),picture.mime or 'image/jpeg'
    covers=tags.get('covr') if hasattr(tags,'get') else None
    if covers:
        cover=covers[0];data=bytes(cover);mime='image/png' if getattr(cover,'imageformat',None)==14 else 'image/jpeg';return data,mime
    encoded=tags.get('metadata_block_picture') if hasattr(tags,'get') else None
    if encoded:
        picture=Picture(base64.b64decode(encoded[0]));return bytes(picture.data),picture.mime or 'image/jpeg'
    return None,None


def write_audio_art(path,data,mime):
    """Replace embedded cover art for ID3, FLAC, MP4 and Vorbis files."""
    import base64
    import mutagen
    from mutagen.flac import Picture
    from mutagen.id3 import APIC
    from mutagen.mp4 import MP4 as MP4Audio,MP4Cover
    from mutagen.oggvorbis import OggVorbis
    try:
        from mutagen.oggopus import OggOpus
    except ImportError:OggOpus=()
    try:
        from mutagen.oggflac import OggFLAC
    except ImportError:OggFLAC=()
    path=Path(path)
    if not data or len(data)>50*1024*1024:raise ValueError('Choose an image smaller than 50 MB')
    media=mutagen.File(str(path),easy=False)
    if media is None:raise ValueError('This audio format does not support embedded artwork')
    tags=media.tags
    if tags is None:media.add_tags();tags=media.tags
    backup=_verified_audio_backup(path)
    if hasattr(tags,'delall') and type(tags).__name__ in ('ID3','ID3Tags'):
        tags.delall('APIC');tags.add(APIC(encoding=3,mime=mime,type=3,desc='Cover',data=data))
    elif hasattr(media,'clear_pictures') and hasattr(media,'add_picture'):
        media.clear_pictures();picture=Picture();picture.data=data;picture.type=3;picture.mime=mime;picture.desc='Cover';media.add_picture(picture)
    elif isinstance(media,MP4Audio):
        fmt=MP4Cover.FORMAT_PNG if mime=='image/png' else MP4Cover.FORMAT_JPEG;tags['covr']=[MP4Cover(data,imageformat=fmt)]
    elif isinstance(media,tuple(x for x in (OggVorbis,OggOpus,OggFLAC) if isinstance(x,type))):
        picture=Picture();picture.data=data;picture.type=3;picture.mime=mime;picture.desc='Cover'
        tags['metadata_block_picture']=[base64.b64encode(picture.write()).decode('ascii')]
    else:raise ValueError('Embedded artwork replacement is not supported for this audio format')
    media.save();return backup


class PlaylistWindow:
    def __init__(self, snapshot, extensions, trace=None, last_played=None):
        self.snapshot = snapshot
        self.trace = trace or (lambda event, **fields: None)
        self.extensions = frozenset(extensions)
        self.events = queue.Queue()
        self.commands = queue.Queue()
        self.lock = threading.Lock()
        self.thread = None
        self.opening = False
        self.last_toggle = 0.0
        self.last_played = last_played
        self.columns = ['number', 'song', 'length', 'last_played']

    def toggle(self):
        with self.lock:
            if time.monotonic() - self.last_toggle < 0.4:
                return
            self.last_toggle = time.monotonic()
            if self.opening:
                self.trace('playlist-window.toggle', target='close')
                self.commands.put('close')
                return
            self.opening = True
            self.trace('playlist-window.toggle', target='open')
            self.thread = threading.Thread(target=self._run, daemon=True, name='playlist-window')
            self.thread.start()

    def close(self):
        with self.lock:
            if self.opening:
                self.trace('playlist-window.shutdown-request')
                self.commands.put('shutdown')

    def _expand(self, paths):
        # Folder enumeration happens off the Tk and player threads.
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                for root, dirs, names in os.walk(path, followlinks=False):
                    dirs.sort(key=str.casefold)
                    for name in sorted(names, key=str.casefold):
                        candidate = Path(root) / name
                        if candidate.suffix.casefold() in self.extensions:
                            self.events.put(('add', str(candidate)))
            elif path.is_file() and path.suffix.casefold() in self.extensions:
                self.events.put(('add', str(path)))

    def _run(self):
        # Tk objects and their cyclic callbacks must be finalized on the thread
        # that owns the Tcl interpreter, before that thread exits.
        try:
            self._run_tk()
        finally:
            import gc
            gc.collect()

    def _run_tk(self):
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            import ctypes
            from ctypes import wintypes
            root = tk.Tk()
            def report_callback_exception(kind, value, tb):
                self.trace('playlist-window.callback-error', error_type=kind.__name__, message=str(value))
                self.events.put(('error', 'Playlist window: ' + str(value)))
            root.report_callback_exception = report_callback_exception
            self.trace('playlist-window.opened')
            root.title('PAFPlayer Playlist Editor')
            root.geometry('660x380')
            root.minsize(340, 180)
            root.configure(bg='#222a35')
            title = tk.Label(root, text='PLAYLIST EDITOR', bg='#222a35', fg='#dcecff', font=('Segoe UI', 10, 'bold'))
            title.pack(fill='x', pady=3)
            header = tk.Label(root, bg='#2d3947', fg='#dcecff', anchor='w', font=('Consolas', 10))
            header.pack(fill='x', padx=6)
            frame = tk.Frame(root, bg='#101820')
            frame.pack(fill='both', expand=True, padx=6)
            bar = tk.Scrollbar(frame)
            bar.pack(side='right', fill='y')
            rows = tk.Listbox(frame, bg='#101820', fg='#b8edb4', selectbackground='#355573', selectforeground='white',
                              activestyle='dotbox', selectmode='extended', exportselection=False, font=('Consolas', 10), yscrollcommand=bar.set)
            rows.pack(side='left', fill='both', expand=True)
            bar.config(command=rows.yview)
            from tkinter import font as tkfont
            list_font = tkfont.Font(root=root, family='Consolas', size=10)
            rows.configure(font=list_font)
            header.configure(font=list_font)
            def zoom_playlist(event):
                delta = int(getattr(event, 'delta', 0) or 0)
                if not delta: return 'break'
                size = max(6, min(32, int(list_font.cget('size')) + (1 if delta > 0 else -1)))
                list_font.configure(size=size)
                return 'break'
            root.bind('<Control-MouseWheel>', zoom_playlist)
            status = tk.StringVar(master=root, value='Ready')
            footer = tk.Frame(root, bg='#222a35')
            footer.pack(fill='x', padx=6, pady=5)
            state = {'paths': (), 'current': None, 'closing': False, 'pending_selection': None, 'drag': None, 'jump_refresh': None}
            durations, labels, extras, requested, priority_requested = {}, {}, {}, set(), set()
            duration_jobs, duration_results = queue.PriorityQueue(), queue.Queue()
            sequence = [0]
            def request_metadata(path, priority):
                if path not in requested or (priority == 0 and path not in priority_requested and path not in labels):
                    requested.add(path)
                    if priority == 0: priority_requested.add(path)
                    sequence[0] += 1; duration_jobs.put((priority, sequence[0], path))
            def duration_worker():
                while True:
                    _, _, path = duration_jobs.get()
                    if path is None: return
                    label, value = metadata_display(path)
                    detail=metadata_extra(path, self.last_played)
                    duration_results.put((path, label, value, detail))
            threading.Thread(target=duration_worker, daemon=True, name='playlist-durations').start()
            column_specs={'number':('#',6),'song':('Song',42),'length':('Length',8),'last_played':('Last played',20),'year':('Year',6),'album':('Album',24),'folder':('Folder',35),'genre':('Genre',18)}
            def cell(value,width):
                value=str(value or '')
                return (value[:width-1]+'…' if len(value)>width else value).ljust(width)
            def row_text(i, path, playing):
                more=extras.get(path,{})
                values={'number':str(i+1),'song':labels.get(path,Path(path).name),'length':durations.get(path,'--:--'),**more}
                return ('>' if playing else ' ')+' '.join(cell(values.get(key,''),column_specs[key][1]) for key in self.columns)
            def refresh_header():
                header.configure(text='  '+' '.join(cell(column_specs[key][0],column_specs[key][1]) for key in self.columns))
            def refresh_rows():
                selected_rows=tuple(rows.curselection());active=rows.index('active') if state['paths'] else 0;anchor=rows.index('anchor') if state['paths'] else 0;y=rows.yview()[0]
                rows.delete(0,'end')
                for i,path in enumerate(state['paths']):
                    playing=os.path.normcase(path)==os.path.normcase(str(state['current'])) and i==state['paths'].index(path)
                    rows.insert('end',row_text(i,path,playing))
                    if playing:rows.itemconfig(i,fg='#fff39a')
                for i in selected_rows:
                    if i<len(state['paths']):rows.selection_set(i)
                if state['paths']:
                    rows.activate(active); rows.selection_anchor(anchor)
                rows.yview_moveto(y);refresh_header()
            def show_column_menu(event):
                menu=tk.Menu(root,tearoff=False)
                for key,(label,_width) in column_specs.items():
                    active=tk.BooleanVar(master=root,value=key in self.columns)
                    def toggle(key=key,active=active):
                        self.columns=[k for k in column_specs if (k in self.columns and k!=key) or (k==key and active.get())]
                        if not self.columns:self.columns=['song']
                        refresh_rows()
                    menu.add_checkbutton(label=label,variable=active,command=toggle)
                menu.tk_popup(event.x_root,event.y_root)
            header.bind('<Button-3>',show_column_menu)
            refresh_header()
            def selected():
                selection = rows.curselection()
                return state['paths'][selection[0]] if selection and selection[0] < len(state['paths']) else None
            def play(event=None):
                if len(rows.curselection()) != 1:
                    status.set('Select exactly one song to play'); return 'break'
                value = selected()
                if value: self.events.put(('play', value))
            def add_files():
                paths = filedialog.askopenfilenames(parent=root, title='Add audio files',
                    filetypes=[('Audio files', ' '.join('*'+e for e in sorted(self.extensions))), ('All files', '*.*')])
                if paths: threading.Thread(target=self._expand, args=(paths,), daemon=True).start()
            def add_folder():
                folder = filedialog.askdirectory(parent=root, title='Add audio folder')
                if folder: threading.Thread(target=self._expand, args=([folder],), daemon=True).start()
            def remove(event=None):
                if len(rows.curselection()) != 1:
                    status.set('Select exactly one song to remove'); return 'break'
                value = selected()
                if not value: return
                answer = messagebox.askyesnocancel('Remove from playlist',
                    'Save this removal to the playlist?\nYes: save  •  No: this session only\nCancel: keep the track', parent=root)
                if answer is not None: self.events.put(('remove', (value, answer)))
            for label, command in [('ADD FILE', add_files), ('ADD DIR', add_folder), ('REMOVE', remove), ('PLAY', play)]:
                tk.Button(footer, text=label, command=command, bg='#3b4655', fg='white', activebackground='#597189').pack(side='left', padx=(0, 4))
            tk.Label(footer, textvariable=status, bg='#222a35', fg='#b8edb4').pack(side='right')
            def edit_tags(event=None):
                indexes=rows.curselection()
                if len(indexes)!=1:
                    status.set('Select exactly one song to edit tags');return 'break'
                path=Path(state['paths'][indexes[0]])
                try:
                    import mutagen
                    media=mutagen.File(str(path),easy=True)
                    if media is None:raise ValueError('Unsupported audio format')
                except Exception as exc:messagebox.showerror('Cannot read tags',str(exc),parent=root);return 'break'
                dialog=tk.Toplevel(root);dialog.title('Edit tags — '+path.name);dialog.transient(root)
                art_panel=tk.Frame(dialog,bg='#1d2733');art_panel.pack(fill='x',padx=10,pady=(10,4))
                art_preview=tk.Label(art_panel,text='Loading album art…',bg='#1d2733',fg='white',width=42,height=12);art_preview.pack(side='left',padx=8,pady=8)
                art_status=tk.Label(art_panel,text='Embedded album art',bg='#1d2733',fg='#d5e5f5',wraplength=260,justify='left');art_status.pack(side='left',padx=8)
                art_state={'photo':None}
                def refresh_art_preview():
                    try:
                        data,mime=read_audio_art(path)
                        if not data:art_preview.configure(image='',text='No embedded album art');art_state['photo']=None;art_status.configure(text='No cover is embedded in this file.');return
                        try:
                            from PIL import Image,ImageTk
                            import io
                            image=Image.open(io.BytesIO(data));image.thumbnail((280,200));photo=ImageTk.PhotoImage(image)
                            art_preview.configure(image=photo,text='');art_state['photo']=photo
                        except ImportError:
                            if mime=='image/png':photo=tk.PhotoImage(data=__import__('base64').b64encode(data));art_preview.configure(image=photo,text='');art_state['photo']=photo
                            else:art_preview.configure(image='',text='Preview needs Pillow');art_state['photo']=None
                        art_status.configure(text=f'Embedded cover · {mime} · {len(data)/1024:.0f} KB')
                    except Exception as exc:art_preview.configure(image='',text='Artwork unavailable');art_status.configure(text='Could not read cover: '+str(exc))
                def replace_art():
                    from tkinter import filedialog
                    image_path=filedialog.askopenfilename(parent=dialog,title='Replace embedded album art',filetypes=[('Images','*.jpg *.jpeg *.png *.webp *.bmp *.gif'),('All files','*.*')])
                    if not image_path:return
                    try:
                        import mimetypes
                        image=Path(image_path);data=image.read_bytes();mime=mimetypes.guess_type(image.name)[0] or 'image/jpeg'
                        if not mime.startswith('image/'):raise ValueError('The selected file is not a recognized image')
                        backup=write_audio_art(path,data,mime);refresh_art_preview();status.set('Album art replaced; backup: '+backup.name)
                    except Exception as exc:messagebox.showerror('Could not replace artwork',str(exc),parent=dialog)
                art_buttons=tk.Frame(art_panel,bg='#1d2733');art_buttons.pack(side='right',padx=8)
                tk.Button(art_buttons,text='Replace album art…',command=replace_art).pack(pady=3)
                tk.Button(art_buttons,text='Refresh preview',command=refresh_art_preview).pack(pady=3)
                refresh_art_preview()
                variables={}
                for key,label in [('title','Title'),('artist','Artist'),('album','Album'),('date','Year'),('genre','Genre'),('tracknumber','Track')]:
                    line=tk.Frame(dialog);line.pack(fill='x',padx=10,pady=3);tk.Label(line,text=label,width=9,anchor='w').pack(side='left')
                    current=media.get(key,[]) if getattr(media,'tags',None) else []
                    var=tk.StringVar(master=dialog,value=str(current[0] if isinstance(current,(list,tuple)) and current else current or ''));variables[key]=var
                    tk.Entry(line,textvariable=var,width=50).pack(side='left',fill='x',expand=True)
                def save_tags():
                    try:
                        backup=write_audio_tags(path,{key:var.get() for key,var in variables.items()})
                    except Exception as exc:messagebox.showerror('Could not save tags',str(exc),parent=dialog);return
                    labels.pop(str(path),None);requested.discard(str(path));priority_requested.discard(str(path));request_metadata(str(path),0)
                    status.set('Tags saved; backup: '+backup.name);dialog.destroy()
                tk.Button(dialog,text='Save tags',command=save_tags).pack(side='left',padx=10,pady=8)
                tk.Button(dialog,text='Cancel',command=dialog.destroy).pack(side='right',padx=10,pady=8)
                return 'break'
            def file_menu(event):
                index=rows.nearest(event.y)
                if index>=len(state['paths']):return 'break'
                if index not in rows.curselection():rows.selection_clear(0,'end');rows.selection_set(index);rows.activate(index)
                count=len(rows.curselection());menu=tk.Menu(root,tearoff=False)
                menu.add_command(label='Edit tags…  Alt+3',command=edit_tags,state='normal' if count==1 else 'disabled')
                menu.add_command(label='Play',command=play,state='normal' if count==1 else 'disabled')
                menu.add_command(label='Remove from playlist…',command=remove,state='normal' if count==1 else 'disabled')
                menu.tk_popup(event.x_root,event.y_root);return 'break'
            root.bind('<Alt-KeyPress-3>',edit_tags)
            rows.bind('<Button-3>',file_menu)
            rows.bind('<Double-Button-1>', play)
            rows.bind('<Return>', play)
            rows.bind('<Delete>', remove)
            def drag_start(event):
                if not state['paths']: return 'break'
                index = rows.nearest(event.y)
                shift, ctrl = bool(event.state & 0x0001), bool(event.state & 0x0004)
                state['drag'] = None
                if shift:
                    anchor = rows.index('anchor')
                    if not ctrl: rows.selection_clear(0, 'end')
                    rows.selection_set(min(anchor, index), max(anchor, index))
                    rows.activate(index)
                    return 'break'
                if ctrl:
                    if index in rows.curselection(): rows.selection_clear(index)
                    else: rows.selection_set(index)
                    rows.selection_anchor(index); rows.activate(index)
                    return 'break'
                selection = tuple(rows.curselection())
                if index not in selection:
                    rows.selection_clear(0, 'end'); rows.selection_set(index)
                    selection = (index,)
                rows.selection_anchor(index); rows.activate(index)
                state['drag'] = (selection, tuple(state['paths']), event.y, index)
                return 'break'
            def drag_motion(event):
                if state['drag'] is None: return 'break'
                if event.y < 0: rows.yview_scroll(-1, 'units')
                elif event.y >= rows.winfo_height(): rows.yview_scroll(1, 'units')
                target = rows.nearest(event.y)
                status.set(f'Move to position {target + 1}')
                return 'break'
            def drag_end(event):
                drag, state['drag'] = state['drag'], None
                if drag is None: return 'break'
                selection, expected, start_y, clicked = drag
                target = rows.nearest(event.y)
                if target not in selection and abs(event.y - start_y) >= 4:
                    _, new_selection = move_rows(expected, selection, target)
                    state['pending_selection'] = new_selection
                    source = selection[0] if len(selection) == 1 else selection
                    self.events.put(('move', (expected, source, target)))
                    status.set('Reordering…')
                else:
                    if abs(event.y - start_y) < 4:
                        rows.selection_clear(0, 'end'); rows.selection_set(clicked)
                        rows.selection_anchor(clicked); rows.activate(clicked)
                    status.set(f'{len(state["paths"])} tracks')
                return 'break'
            rows.bind('<ButtonPress-1>', drag_start)
            rows.bind('<B1-Motion>', drag_motion)
            rows.bind('<ButtonRelease-1>', drag_end)
            def open_jump(event=None):
                dialog = tk.Toplevel(root); dialog.title('Jump to track'); dialog.geometry('620x420')
                dialog.configure(bg='#222a35'); dialog.transient(root)
                query = tk.StringVar(master=dialog)
                entry = tk.Entry(dialog, textvariable=query); entry.pack(fill='x', padx=8, pady=8)
                box = tk.Listbox(dialog, bg='#101820', fg='#b8edb4', selectbackground='#355573', exportselection=False, font=('Consolas', 10))
                box.pack(fill='both', expand=True, padx=8)
                hint = tk.Label(dialog, text='Type to filter • Enter or double-click to play • Escape to cancel', bg='#222a35', fg='white'); hint.pack(pady=5)
                matches = []
                def refresh(*unused):
                    previous = matches[box.curselection()[0]] if box.curselection() and box.curselection()[0] < len(matches) else None
                    words = query.get().casefold().split()
                    matches[:] = [path for path in state['paths'] if all(word in (labels.get(path, '') + ' ' + path).casefold() for word in words)][:1000]
                    box.delete(0, 'end')
                    for path in matches: box.insert('end', labels.get(path, Path(path).name))
                    index = matches.index(previous) if previous in matches else 0
                    if matches: box.selection_set(index); box.activate(index)
                def accept(event=None):
                    selected_rows = box.curselection()
                    if selected_rows and selected_rows[0] < len(matches):
                        self.events.put(('play', matches[selected_rows[0]])); dialog.destroy()
                    return 'break'
                def dismiss(event=None): dialog.destroy(); return 'break'
                def down(event):
                    if matches: box.focus_set()
                    return 'break'
                query.trace_add('write', refresh)
                box.bind('<Double-Button-1>', accept); box.bind('<Return>', accept)
                entry.bind('<Return>', accept); entry.bind('<Down>', down)
                dialog.bind('<Escape>', dismiss)
                state['jump_refresh'] = refresh
                dialog.bind('<Destroy>', lambda event: state.__setitem__('jump_refresh', None) if event.widget is dialog else None)
                refresh(); entry.focus_set()
                return 'break'
            def jump_key(event):
                if isinstance(event.widget, (tk.Entry, tk.Text)) or state['jump_refresh'] is not None: return None
                return open_jump(event)
            root.bind('<Control-o>', lambda event: (self.events.put(('open-playlist', None)), 'break')[1])
            root.bind('<KeyPress-j>', jump_key)
            root.bind('<KeyPress-J>', jump_key)
            rows.focus_set()
            def close(reason):
                if not state['closing']:
                    self.trace('playlist-window.close', reason=reason)
                    state['closing'] = True
                    self.last_toggle = time.monotonic()
                    duration_jobs.put((-1, 0, None))
                    for hwnd, old_proc, callback in hooks:
                        shell32.DragAcceptFiles(hwnd, False)
                        setproc(hwnd, -4, old_proc)
                    root.destroy()
            root.protocol('WM_DELETE_WINDOW', lambda: close('window-manager'))
            # Both playlist shortcuts belong to this window while it has focus.
            held = [False]
            def alt_p(event):
                if not held[0]: held[0] = True; close('ctrl-alt-p' if event.state & 0x0004 else 'alt-p')
                return 'break'
            root.bind('<Alt-KeyPress-p>', alt_p)
            root.bind('<Control-Alt-KeyPress-p>', alt_p)
            root.bind('<Alt-KeyRelease-p>', lambda event: held.__setitem__(0, False))
            root.bind('<Control-Alt-KeyRelease-p>', lambda event: held.__setitem__(0, False))
            # Native WM_DROPFILES requires no optional tkinterdnd dependency.
            hooks = []
            if os.name == 'nt':
                user32, shell32 = ctypes.windll.user32, ctypes.windll.shell32
                LRESULT = ctypes.c_ssize_t
                WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
                setproc = user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.SetWindowLongW
                setproc.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]; setproc.restype = ctypes.c_void_p
                user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
                user32.CallWindowProcW.restype = LRESULT
                shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
                shell32.DragQueryFileW.restype = wintypes.UINT
                shell32.DragFinish.argtypes = [wintypes.HANDLE]
                shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
                root.update_idletasks()
                for widget in (root, rows):
                    hwnd = widget.winfo_id()
                    old = [None]
                    def proc(h, msg, wp, lp, old=old):
                        if msg == 0x233:
                            paths = []
                            try:
                                count = shell32.DragQueryFileW(wp, 0xffffffff, None, 0)
                                for i in range(count):
                                    size = shell32.DragQueryFileW(wp, i, None, 0)
                                    buf = ctypes.create_unicode_buffer(size+1)
                                    shell32.DragQueryFileW(wp, i, buf, size+1)
                                    paths.append(buf.value)
                            finally: shell32.DragFinish(wp)
                            threading.Thread(target=self._expand, args=(paths,), daemon=True).start()
                            return 0
                        return user32.CallWindowProcW(old[0], h, msg, wp, lp)
                    callback = WNDPROC(proc)
                    old[0] = setproc(hwnd, -4, ctypes.cast(callback, ctypes.c_void_p))
                    if old[0]:
                        shell32.DragAcceptFiles(hwnd, True)
                        hooks.append((hwnd, old[0], callback))
            def poll():
                try:
                    command = self.commands.get_nowait()
                except queue.Empty: command = None
                if command in ('close', 'shutdown'):
                    close('toggle' if command == 'close' else 'player-shutdown'); return
                try:
                    paths, current = self.snapshot()
                    paths = tuple(str(p) for p in paths)
                    if paths != state['paths'] or str(current) != state['current']:
                        old_paths = state['paths']; selected_indices = tuple(rows.curselection())
                        old_anchor = rows.index('anchor') if old_paths else 0
                        y = rows.yview()[0]
                        selected_indices = remap_selection(old_paths, paths, selected_indices)
                        mapped_anchor = remap_selection(old_paths, paths, (old_anchor,))
                        state['paths'], state['current'] = paths, str(current)
                        rows.delete(0, 'end')
                        current_index = -1
                        for i, path in enumerate(paths):
                            playing = os.path.normcase(path) == os.path.normcase(str(current)) and current_index < 0
                            if playing: current_index = i
                            rows.insert('end', row_text(i, path, playing))
                            if playing: rows.itemconfig(i, fg='#fff39a')
                        pending = state['pending_selection']
                        if pending is not None:
                            selected_indices = tuple(i for i in pending if 0 <= i < len(paths))
                            state['pending_selection'] = None
                        for index in selected_indices: rows.selection_set(index)
                        if selected_indices:
                            anchor = mapped_anchor[0] if mapped_anchor and pending is None else selected_indices[0]
                            rows.selection_anchor(anchor); rows.activate(selected_indices[-1]); rows.yview_moveto(y)
                        elif not old_paths and current_index >= 0:
                            rows.selection_set(current_index); rows.selection_anchor(current_index)
                            rows.activate(current_index); rows.see(current_index)

                        status.set(f'{len(paths)} tracks')
                    updated = False
                    selected_before = tuple(rows.curselection())
                    active_before = rows.index('active') if paths else 0
                    anchor_before = rows.index('anchor') if paths else 0
                    y_before = rows.yview()[0]
                    for _ in range(30):
                        try: path, label, duration, detail = duration_results.get_nowait()
                        except queue.Empty: break
                        labels[path] = label; durations[path] = duration; extras[path] = detail; updated = True
                        # Refresh text without changing the selected row.
                        for i in (j for j, item in enumerate(paths) if item == path):
                            playing = os.path.normcase(path) == os.path.normcase(str(current)) and i == paths.index(path)
                            rows.delete(i); rows.insert(i, row_text(i, path, playing))
                            if playing: rows.itemconfig(i, fg='#fff39a')
                    if updated:
                        rows.selection_clear(0, 'end')
                        for selected_index in selected_before: rows.selection_set(selected_index)
                        if paths:
                            rows.activate(active_before); rows.selection_anchor(anchor_before)
                        rows.yview_moveto(y_before)
                    if paths:
                        first = rows.nearest(0)
                        last = min(len(paths), first + max(20, rows.winfo_height() // 14 + 3))
                        for path in paths[first:last]:
                            request_metadata(path, 0)
                        # Queue the remainder without I/O on this thread.
                        for path in paths: request_metadata(path, 1)
                    if updated and state['jump_refresh'] is not None: state['jump_refresh']()
                except Exception as exc:
                    status.set(str(exc)[:80])
                root.after(350, poll)
            poll()
            root.mainloop()
        except Exception as exc:
            self.trace('playlist-window.failure', error_type=type(exc).__name__, message=str(exc))
            self.events.put(('error', 'Playlist window: ' + str(exc)))
        finally:
            with self.lock:
                self.opening = False
                while True:
                    try: self.commands.get_nowait()
                    except queue.Empty: break
            self.trace('playlist-window.finished')
            self.events.put(('closed', None))
