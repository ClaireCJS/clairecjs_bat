"""Four actual Windows processes, shell icons and native artwork messages."""
import ctypes
import json,os,queue,subprocess,sys,threading,time,uuid
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from image_caption_gender_fixer import artwork_shell
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from test_images import ROOT,app_for


CHILD=r'''
import ctypes,json,os,queue,sys,threading
from pathlib import Path
from ctypes import wintypes as w
sys.path[:0]=[sys.argv[1],sys.argv[2]]
handles=[os.add_dll_directory(str(Path(sys.argv[2])/part)) for part in ('numpy.libs','PIL','cv2','.dlls') if (Path(sys.argv[2])/part).is_dir()]
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.artwork_shell import native
viewer=AlbumArtReview([{'path':sys.argv[3],'title':'Instance '+sys.argv[5]}],floating=True,shell_group=sys.argv[4])
viewer.root.geometry('680x480+'+str(20+int(sys.argv[5])*35)+'+20')
commands=queue.Queue()
def read_commands():
    pending=b''
    while True:
        data=os.read(sys.stdin.fileno(),4096)
        if not data:return
        pending+=data
        while b'\n' in pending:
            line,pending=pending.split(b'\n',1);commands.put(line.decode().rstrip('\r'))
threading.Thread(target=read_commands,daemon=True).start()
c,w,user,shell,_,_,_,_,_=native()
user.IsWindowVisible.argtypes=[w.HWND];user.IsWindowVisible.restype=w.BOOL
get_id=shell.GetCurrentProcessExplicitAppUserModelID
get_id.argtypes=[c.POINTER(w.LPWSTR)];get_id.restype=w.LONG
def state(kind):
    viewer.root.update_idletasks();native_shell=viewer.window_shell
    _,hwnd,getter,_=viewer._native_window()
    pointer=w.LPWSTR();assert get_id(c.byref(pointer))==0
    appid=pointer.value
    ole=c.WinDLL('ole32');ole.CoTaskMemFree.argtypes=[c.c_void_p];ole.CoTaskMemFree(c.cast(pointer,c.c_void_p))
    print(json.dumps({'kind':kind,'pid':os.getpid(),'hwnd':hwnd,'visible':bool(user.IsWindowVisible(hwnd)),
          'tray':native_shell.tray_added,'rect':native_shell.tray_rect(),'style':getter(hwnd,-20),
          'appid':appid,'tip':native_shell.tip}),flush=True)
def start():viewer.hide();state('ready')
def poll():
    try:
        while True:
            command=commands.get_nowait()
            if command=='stop':viewer.choose('c');return
            if command=='hide':viewer.hide()
            if command=='all':viewer.show_all_artwork()
            if command=='tray':user.PostMessageW(viewer.window_shell.hwnd,viewer.window_shell.callback_message,1,0x202)
            if command=='state':state('state')
    except queue.Empty:pass
    viewer.root.after(25,poll)
viewer.root.after(50,start);viewer.root.after(25,poll);viewer.show()
print(json.dumps({'kind':'closed'}),flush=True)
'''


def test_four_processes_have_separate_taskbar_and_tray_entries_and_show_all(tmp_path):
    source_root=Path(artwork_shell.__file__).parents[1]
    image=tmp_path/'neutral.png';Image.new('RGB',(180,200),'navy').save(image)
    group=artwork_shell.GROUP+'.Test.'+uuid.uuid4().hex
    processes=[];inboxes=[]
    def output_reader(process,inbox):
        for line in process.stdout:
            try:inbox.put(json.loads(line))
            except ValueError:inbox.put({'unexpected':line})
        inbox.put({'eof':True})
    def read(index,timeout=45):
        try:return inboxes[index].get(timeout=timeout)
        except queue.Empty:raise AssertionError('Artwork process timed out: '+str(index))
    def command(index,value):
        processes[index].stdin.write(value+'\n');processes[index].stdin.flush()
    def states():
        for index in range(4):command(index,'state')
        return [read(index) for index in range(4)]
    try:
        for index in range(4):
            process=subprocess.Popen([sys.executable,'-B','-I','-S','-u','-c',CHILD,str(source_root),str(ROOT/'environment/packages'),str(image),group,str(index)],
                                     stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            inbox=queue.Queue();processes.append(process);inboxes.append(inbox)
            threading.Thread(target=output_reader,args=(process,inbox),daemon=True).start()
        ready=[read(index) for index in range(4)]
        print('Four native artwork instances:',json.dumps(ready))
        assert all(item.get('kind')=='ready' for item in ready),ready
        assert len({item['pid'] for item in ready})==len({item['hwnd'] for item in ready})==4
        assert len({item['appid'] for item in ready})==4
        assert all(item['style']&0x40000 and item['tray'] and not item['visible'] for item in ready),ready
        assert set(artwork_shell.windows(group))=={item['hwnd'] for item in ready}
        deadline=time.monotonic()+8
        observed=states()
        while not all(item['rect'] for item in observed) and time.monotonic()<deadline:
            time.sleep(.1);observed=states()
        assert all(item['rect'] for item in observed),observed
        # The same native reveal signal used by the console shortcut reaches all four.
        assert artwork_shell.reveal_all(group)==4
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            observed=states()
            if all(item['visible'] for item in observed):break
            time.sleep(.05)
        assert all(item['visible'] and item['tray'] for item in observed),observed
        # A tray click restores only its owner; the artwork's show-all path restores peers.
        for index in range(4):command(index,'hide')
        assert not any(item['visible'] for item in states())
        command(2,'tray');deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            observed=states()
            if observed[2]['visible']:break
            time.sleep(.05)
        assert [item['visible'] for item in observed]==[False,False,True,False]
        command(2,'all');time.sleep(.2)
        assert all(item['visible'] for item in states())
    finally:
        for process in processes:
            if process.poll() is None:
                try:process.stdin.write('stop\n');process.stdin.flush()
                except OSError:pass
        for process in processes:
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        errors=[process.stderr.read() for process in processes]
        assert all(process.returncode==0 for process in processes),errors
    assert artwork_shell.windows(group)==[]


def test_console_active_reopen_reveals_peer_instances_but_passive_reopen_does_not(tmp_path,monkeypatch):
    calls=[]
    class Art:
        def reopen(self,activate=False):calls.append(('own',activate))
    app=app_for(tmp_path);app.floating_artwork=Art()
    monkeypatch.setattr(artwork_shell,'reveal_all',lambda **kw:calls.append(('peers',kw)))
    app.reopen_artwork(False);assert calls==[('own',False)]
    app.reopen_artwork(True)
    assert calls[1:]==[('own',True),('peers',{'exclude_pid':os.getpid()})]


def test_artwork_a_g_r_and_file_keys_use_correct_actions_and_dialog_defaults(tmp_path,monkeypatch):
    from tkinter import simpledialog,messagebox
    image=tmp_path/'source.png';Image.new('RGB',(200,200),'navy').save(image)
    viewer=AlbumArtReview([{'path':str(image),'title':'Review'}],{'detected':'old','proposed':'new'},floating=True)
    actions=[];questions=[]
    def event(char='',keysym=''):return SimpleNamespace(widget=viewer.canvas,state=0,char=char,keysym=keysym or char)
    def review():
        viewer._has_drawn=True;viewer._dirty=False
        viewer.set_review(actions.append,[],False,changes=[{'index':0,'before':'old','after':'new'}],source=str(image))
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw();review()
        assert '[A]' in viewer.buttons['a'].cget('text') and '[G]' in viewer.buttons['edit_caption'].cget('text')
        viewer.button_hotkey(event('a'));assert actions==['a']
        review();viewer.button_hotkey(event('g'));assert actions[-1]=={'action':'edit_caption','text':'new'}
        review();viewer.button_hotkey(event('r'));assert actions[-1]=='s'
        review()
        def ask(*args,**kwargs):questions.append(kwargs);return 'edited name.png'
        monkeypatch.setattr(simpledialog,'askstring',ask);viewer.button_hotkey(event(keysym='F2'))
        assert questions[0]['initialvalue']=='source.png'
        assert actions[-1]=={'action':'rename_image','source':str(image),'name':'edited name.png'}
        review();before=list(actions)
        def decline(*args,**kwargs):questions.append(kwargs);return False
        monkeypatch.setattr(messagebox,'askyesno',decline);viewer.button_hotkey(event(keysym='Delete'))
        assert actions==before and image.exists() and questions[-1]['default']=='no'
        monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kwargs:True)
        viewer.button_hotkey(event(keysym='Delete'))
        assert actions[-1]=={'action':'recycle_image','source':str(image),'confirmed':True}
        # Text editing never dispatches image actions.
        review();key=event(keysym='Delete');key.widget=viewer.proposed_caption;before=list(actions)
        viewer.button_hotkey(key);assert actions==before
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_tray_recreation_and_cleanup_use_native_icon_lifecycle(tmp_path,monkeypatch):
    image=tmp_path/'image.png';Image.new('RGB',(200,200),'navy').save(image)
    group=artwork_shell.GROUP+'.Test.'+uuid.uuid4().hex
    viewer=AlbumArtReview([{'path':str(image),'title':'Review'}],floating=True,shell_group=group)
    shell=viewer.window_shell;calls=[];original=shell.shell.Shell_NotifyIconW
    def notify(action,data):calls.append(action);return original(action,data)
    monkeypatch.setattr(shell.shell,'Shell_NotifyIconW',notify)
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        assert shell.tray_added and shell.tray_rect() is not None
        # Simulate Explorer removing just this test icon before its restart notice.
        data=shell.icon_data();assert original(2,ctypes.byref(data))
        shell.dispatch(shell.hwnd,shell.explorer,0,0,0,0)
        assert not calls
        shell.poll();assert 0 in calls and shell.tray_added and shell.tray_rect() is not None
        shell.close();assert calls[-1]==2 and shell.tray_rect() is None
        assert shell not in artwork_shell._live_shells and artwork_shell.windows(group)==[]
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_f2_inside_unchanged_caption_prefills_name_and_invalid_name_stays_in_review(tmp_path,monkeypatch):
    from tkinter import simpledialog,messagebox
    image=tmp_path/'source.png';Image.new('RGB',(200,200),'navy').save(image)
    viewer=AlbumArtReview([{'path':str(image),'title':'Review'}],floating=True)
    actions=[];errors=[];questions=[]
    try:
        viewer.set_review(actions.append,[],False,changes=[],source=str(image))
        def ask(*args,**kwargs):questions.append(kwargs);return '../escape.png'
        monkeypatch.setattr(simpledialog,'askstring',ask)
        monkeypatch.setattr(messagebox,'showerror',lambda *args,**kwargs:errors.append(args))
        event=SimpleNamespace(widget=viewer.proposed_caption,state=0,char='',keysym='F2')
        viewer.button_hotkey(event)
        assert questions[0]['initialvalue']=='source.png' and errors and not actions and image.exists()
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_tray_menu_survives_posting_and_its_show_all_command_is_usable(tmp_path,monkeypatch):
    image=tmp_path/'image.png';Image.new('RGB',(200,200),'navy').save(image)
    viewer=AlbumArtReview([{'path':str(image),'title':'Review'}],floating=True)
    calls=[];shell=viewer.window_shell
    try:
        monkeypatch.setattr(viewer.tk.Menu,'tk_popup',lambda menu,*args:calls.append('posted'))
        monkeypatch.setattr(viewer,'show_all_artwork',lambda:calls.append('all'))
        shell.tray_menu();menu=shell.menu
        assert menu.winfo_exists() and calls==['posted']
        assert [menu.entrycget(i,'label') for i in range(3)]==['Show this artwork','Show all ICGF artwork','Hide this artwork']
        menu.invoke(1);assert calls==['posted','all']
        shell.close();assert shell.menu is None and not menu.winfo_exists()
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
