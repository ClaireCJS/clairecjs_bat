import tkinter as tk
from screeninfo import get_monitors
import keyboard

def close_windows(e): root.quit()

def main():
    global root
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(background='black')

    for monitor in get_monitors():
        window = tk.Toplevel(root)
        window.overrideredirect(True)
        window.configure(background='black')
        window.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")

    keyboard.on_press_key("q", close_windows)
    root.mainloop()

if __name__ == '__main__':
    main()

