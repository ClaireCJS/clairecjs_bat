"""Before/After click gestures and a delayed, passive artwork tooltip."""
from pathlib import Path
import os


class ArtworkClicks:
    HOVER_MS=2000
    HELP='Single click: toggle Before / After.\nTriple click: open the displayed image in your default image viewer.'

    def __init__(self,viewer):
        self.viewer=viewer;self.pair=None;self.click_timer=None;self.hover_timer=None
        self.tooltip=None;self.position=(0,0)
        self.click_ms=500
        if os.name=='nt':
            import ctypes
            self.click_ms=max(150,min(1500,int(ctypes.windll.user32.GetDoubleClickTime())))
        canvas=viewer.canvas
        canvas.bind('<Button-1>',self.click)
        canvas.bind('<Double-Button-1>',self.click)
        canvas.bind('<Triple-Button-1>',self.triple)
        canvas.bind('<Enter>',self.enter)
        canvas.bind('<Motion>',self.motion)
        canvas.bind('<Leave>',self.leave)

    def cancel_click(self):
        if self.click_timer is not None:
            self.viewer.root.after_cancel(self.click_timer);self.click_timer=None

    def hide_tooltip(self):
        if self.hover_timer is not None:
            self.viewer.root.after_cancel(self.hover_timer);self.hover_timer=None
        if self.tooltip is not None:
            self.tooltip.destroy();self.tooltip=None

    def reset(self):
        self.cancel_click();self.hide_tooltip();self.pair=None

    def comparison(self,source,blocked):
        """The review supplies the source; the displayed full proposal is After."""
        if blocked:return
        source=Path(source)
        if self.pair is not None and Path(self.pair[0]['path'])==source:return
        current=self.viewer.views[self.viewer.selector.current()]
        if Path(current['path'])==source:return
        before={'path':str(source),'title':'Before — original image'}
        after=dict(current,title='After — proposed corrected image')
        self.pair=(before,after)
        self.viewer.views=[before,after]
        self.viewer.selector.configure(values=['1. '+before['title'],'2. '+after['title']])
        self.viewer.selector.current(1)

    def click(self,event=None):
        self.hide_tooltip();self.cancel_click()
        if event is not None:self.viewer.activate_on_click(event)
        # A second click postpones the toggle; a third cancels it altogether.
        self.click_timer=self.viewer.root.after(self.click_ms,self.toggle)
        return 'break'

    def toggle(self):
        self.click_timer=None
        if self.pair is None:return
        index=self.viewer.selector.current()
        self.viewer.selector.current(0 if index==1 else 1)
        self.viewer.schedule_draw()

    def triple(self,event=None):
        self.cancel_click();self.hide_tooltip()
        if event is not None:self.viewer.activate_on_click(event)
        return self.viewer.open_default_viewer(event)

    def enter(self,event):
        self.hide_tooltip();self.position=(event.x_root,event.y_root)
        self.hover_timer=self.viewer.root.after(self.HOVER_MS,self.show_tooltip)

    def motion(self,event):self.position=(event.x_root,event.y_root)

    def leave(self,event=None):self.hide_tooltip()

    def show_tooltip(self):
        self.hover_timer=None
        if self.viewer.root.state() in ('withdrawn','iconic'):return
        with self.viewer._activation:
            tip=self.viewer.tk.Toplevel(self.viewer.root);tip.withdraw();tip.overrideredirect(True)
            self.tooltip=tip
            text=self.HELP
            if self.pair is None:text+='\nAfter becomes available when a corrected preview is ready.'
            label=self.viewer.tk.Label(tip,text=text,justify='left',bg='#fff4bc',fg='#161616',
                                       relief='solid',borderwidth=1,padx=8,pady=6,wraplength=380)
            label.pack();tip.update_idletasks()
            x,y=self.position
            areas=self.viewer.backend.monitors() or [(0,0,tip.winfo_screenwidth(),tip.winfo_screenheight())]
            area=next((area for area in areas if area[0]<=x<area[2] and area[1]<=y<area[3]),areas[0])
            x=max(area[0]+4,min(x+16,area[2]-tip.winfo_reqwidth()-4))
            y=max(area[1]+4,min(y+20,area[3]-tip.winfo_reqheight()-4))
            tip.geometry(f'{x:+d}{y:+d}');tip.deiconify();tip.update_idletasks()

    def close(self):self.reset()
