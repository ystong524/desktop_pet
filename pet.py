"""
TODO:
[done] add stationary, dragging modes
[pending] add more complex moving pattern-->zigzag, labyrinth-like
[done] switching between modes-->switch to xx when stationary for certain period
[pending] manage when to switch mdoes--> added random, pending sequence
[pending] scaling, speed to be decided during init of class

DEBUG:
[done] window event callback run twice
--should bind at label level (self._label) instead of self._window
--see: https://stackoverflow.com/a/71187557
--see: https://www.astro.princeton.edu/~rhl/Tcl-Tk_docs/tk/bind.n.html
[pending] smoothen drag mode
[pending] right button event seems to involve enter & leave events
[pending] in random mode, avoid out of screen for too long?

THINK:
in case of stationary mode, use a bool variable to bypass time comparison route
--resolution when switching mode will be dependent on window mainloop interval
--but need to establish/check relation between self._mms items with the bool
or
use similar update route but do nothing
--self._x_incre, self._y_incre = 0, 0
--set self._pattern_dur = 1 (this will be the resolution to detect change in mode)
"""

##ref: https://seebass22.github.io/python-desktop-pet-tutorial/2021/05/16/desktop-pet.html
import tkinter as tk
import time
import random
from win32api import GetSystemMetrics, GetMonitorInfo, MonitorFromPoint
import os
import sys

""" ------- path redirect for pyinstaller use -------
https://stackoverflow.com/a/60953781
"""
def resource_path(path_name):
    """ return absolute path for resources located at relative
        to the directory of this script or sys._MEIPASS"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, path_name)


""" ------- window size ------- """
def get_win_geometry(exclude_taskbar=False):
    if exclude_taskbar:
        monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
        work_area = monitor_info.get("Work")
        return work_area[2], work_area[3]
    else:
        return GetSystemMetrics(0), GetSystemMetrics(1)

""" ------- motion pattern -------
functions that return x, y increment steps for window movement
return (x[int], y[int])
"""
def random_motion(x_lower=1, x_upper=10, y_lower=1, y_upper=10):
    ##random for both x and y
    return random_direct_step(lower=x_lower, upper=x_upper),\
           random_direct_step(lower=y_lower, upper=y_upper)

def random_direct_step(lower=1, upper=10):
    """
    return a numerical value symbolizing
    direction (backward-, stationary 0, forward +) and steps to be taken
    """
    direct = random.choice([-1, 1])
    if direct == 0:  ##TODO: allow stationary?
        return 0
    step = random.randrange(lower, upper)
    return direct * step

def random_small():
    return random_motion(x_lower=1, x_upper=5, y_lower=1, y_upper=5)

def random_large():
    return random_motion(x_lower=10, x_upper=30, y_lower=10, y_upper=30)

def stationary():
    return 0, 0

""" ------- gif source ------- """
def extract_gif(gif_src):
    frame_num = 0
    while True:
        try:
            temp = tk.PhotoImage(file=gif_src, format="gif -index {}".format(frame_num))
        except Exception as e:
            break
        else:
            frame_num += 1
    assert frame_num > 0, "GIF has no frames"
    gif = [tk.PhotoImage(file=gif_src,
                         format="gif -index {}".format(i)) for i in range(frame_num)]
    return gif

""" ------- tkinter window ------- """
class Window(object):
    def __init__(self, img_src=None, gif_src=None,
                 exclude_taskbar=True, lim_w=30, lim_h=30,
                 print_fn=None):
        ##init window
        self._window = tk.Tk()
        self._window.config(highlightbackground="black")  ##set focushighlight black when not focused
        self._window.overrideredirect(True)  ##make frameless
        self._window.attributes("-topmost", True)  ##top level
        self._window.wm_attributes("-transparentcolor", "black")  ##turn black into transparent
        
        ##arguments
        self._img_src = img_src
        self._gif_src = gif_src
        self._exclude_taskbar = exclude_taskbar
        self._lim_w = lim_w
        self._lim_h = lim_h
        self._print_fn = print_fn
        if self._print_fn is None:
            def empty(*a):
                return
            self._print_fn = empty
        
        ##internal variables
        ##display use
        self._img = None
        self._gif = None
        self._win_w, self._win_h = get_win_geometry(exclude_taskbar=self._exclude_taskbar)
        self._frame_num = 1
        self._frame_id = 0
        ##update mechanism
        self._pattern_time = time.time()
        self._pattern_dur = round(random.random() * 10, 2)
        self._time = time.time()
        ##initial position, ensure within screen frame
        self._x = random.randrange(int(0.2*self._win_w), int(0.8*self._win_w))
        self._y = random.randrange(int(0.2*self._win_h), int(0.8*self._win_h))
        self._x_incre = 0
        self._y_incre = 0
        ##control motion change
        self._mode = 0
        self._last_mode = 0
        self._random_mode = False
        self._stationary = False
        self._stationary_ts = None
        self._drag = False
        self._mms = {0: stationary, 1: random_small, 2: random_large, 3: stationary}  ##movement modes
        ##control gif change
        self._gif_dict = {}
        self._gif_key_id = 0
        
        ##count gif frames
        if not self._gif_src is None:
            if type(self._gif_src) in [list, tuple]:  ##list of paths
                if type(self._gif_src[0]) == str:
                    count = 0
                    for path in self._gif_src:
                        if os.path.exists(path):
                            self._gif_dict[count] = extract_gif(path)
                            count += 1
                        else:
                            self._print_fn("WARNING: {} not found".format(path))
                    self._gif = self._gif_dict[0]
                    self._img = self._gif[0]
                    
                else:
                    raise ValueError("gif_src can only be a list of paths or single path")
                
            elif type(self._gif_src) == str:  ##single path
                self._gif = extract_gif(self._gif_src)
                self._img = self._gif[0]
                self._gif_dict = {0: self._gif}
            else:
                raise ValueError("gif_src can only be a list of paths or single path")
            
        else:  ##single image
            self._img = tk.PhotoImage(file=self._img_src)
            self._gif = [self._img]
            self._gif_dict = {0: self._gif}
        
        ##update after parsing gif files
        self._frame_num = len(self._gif)
        self._gif_key_id = 0  ##default take the first
        self._change_mode(1)##default in random_small
        
        ##check img file
        assert not (self._img is None), "Image / GIF file failed to load"
        
        ##image label
        self._label = tk.Label(self._window, bd=0, bg="black")
        
        ##geometry and display label
        self._update_win_pos()
        
        ##label event bind
        def mode_func(self, mode_key, name, overwrite=False):
            def change_mode(*event):
                self._change_mode(mode_key, overwrite=overwrite)
                self._print_fn("change mode", name)
            return change_mode
        
        self._label.bind("<Button-1>", self._change_gif)
        self._label.bind("<Enter>", mode_func(self, 0, "stationary"))
        self._label.bind("<Leave>",  self._resume_mode)
        self._label.bind("<Button-3>", self._menu_popup)
        self._label.bind("<B1-Motion>", self._drag_func)
        self._label.bind("<ButtonRelease-1>", self._drag_release)
        
        ##label menu
        ##https://www.geeksforgeeks.org/right-click-menu-using-tkinter/
        self._menu = tk.Menu(self._window, tearoff=0)
        self._menu.add_command(label="Random", command=self._set_random)
        self._menu.add_command(label="Stay", command=mode_func(self, 0, "stationary", overwrite=True))
        self._menu.add_command(label="Float", command=mode_func(self, 1, "random_small", overwrite=True))
        self._menu.add_command(label="Chase", command=mode_func(self, 2, "random_large", overwrite=True))
        self._menu.add_command(label="Drag", command=mode_func(self, 3, "drag", overwrite=True))
        self._menu.add_command(label="Exit", command=self._window.destroy)
        
        ##mainloop
        self._update()  ##init call, else window shown packed without image update in a glimpse
#        self._time = time.time()  ##update time now
#        while not(self._x_incre or self._y_incre):  ##skip this if initial mode is stationary
#            self._moving_pattern()  ##first pattern
#        self._window.after(0, self._update)  ##run ._update now to start the recursive loop
        
        #self._window.withdraw()
        #self._window.deiconify()
#        self._window.protocol("WM_DELETE_WINDOW", self._window.iconify)
        self._window.mainloop()  ##start window loop here
    
    def _update_win_pos(self):
        if self._stationary or self._drag:
            return
        
        if self._x_incre or self._y_incre:
            ##update steps
            self._x += self._x_incre
            self._y += self._y_incre
        else:
            return  ##skip calculation if stationary
        
        ##ensure within screen boundaries
        ##allow exceeding at some limits/change motion
        img_w = self._img.width()
        img_h = self._img.height()
        
        x_cross = (self._x - self._win_w)
        y_cross = (self._y - self._win_h)
        if self._x < 0:
            if x_cross < (0-self._lim_w-img_w):
                self._x = self._win_w
        else:
            if x_cross > self._lim_w:
                self._x = 0
                
        if self._y < 0:
            if y_cross < (0-self._lim_h-img_h):
                self._y = self._win_h
        else:
            if y_cross > self._lim_h:
                self._y = 0
                
        self._window.geometry("{w}x{h}+{x}+{y}".format(w=img_w, h=img_h,
                                                       x=self._x, y=self._y))  ##we're moving window
        
    def _update_image(self, zoom=True, scale=1):
        self._frame_id = (self._frame_id + 1) % self._frame_num
        if scale != 1:  ##TODO: scaling during init of class
            if zoom:
                self._img = self._gif[self._frame_id].zoom(scale, scale)
            else:
                self._img = self._gif[self._frame_id].subsample(scale, scale)
        else:
            self._img = self._gif[self._frame_id]
            
        self._label.configure(image=self._img)
        self._label.pack()
        
    def _update(self):
        ##motion pattern
        ##if current time surpass last pattern duration, obtain a new pattern
        if not self._stationary:  ##use a bool here, save some computation
            if (time.time() - self._pattern_time) > self._pattern_dur:
                self._moving_pattern()  ##obtain x,y increment based on motion mode
                if self._random_mode:
                    if random.choice([0, 1]):  ##random choose gif images
                        self._print_fn("random gif")
                        self._change_gif(None, num=random.randrange(1, len(self._gif_dict)-1))
        else:
            if (time.time() - self._stationary_ts) > 5:  ##change to random_small mode after 5 seconds of stationary mode
                self._print_fn("break stationary")
                self._change_mode(1, overwrite=False)
            
        ##update gif image frame
        if (time.time() - self._time) > 0.05:  ##TODO: skip addition every loop, instead add on the _time
            self._time = time.time()  ##TODO: refresh time first or frame
            
            ##update window and label (boundary control)
            self._update_win_pos()
            
            ##update to image (frame & scale control)
            self._update_image(zoom=True, scale=1)
        
        ##execute update
        self._window.after(10, self._update)  ##call ._update recursively
    
    def _moving_pattern(self):
        if self._random_mode:
            self._print_fn("random mode")
            self._change_mode(random.choice([0, 1, 2]))
        self._x_incre, self._y_incre = self._mms[self._mode]()
        if self._x_incre or self._y_incre:
            self._pattern_dur = round(random.random() * 10, 2)
        else:
            self._pattern_dur = 1
        self._pattern_time = time.time()
        self._print_fn("pattern", self._pattern_dur, self._x_incre, self._y_incre)
    
    def _drag_func(self, event):
        if self._drag:
            w = self._img.width()
            h = self._img.height()
            self._x = event.x_root-w//2
            self._y = event.y_root-h//2
            self._window.geometry("{w}x{h}+{x}+{y}".format\
                                  (w=w, h=h, x=self._x, y=self._y))  ##we're moving window
            
    def _drag_release(self, event):
        self._change_mode(0, overwrite=True)
        self._print_fn("release stationary")
    
    def _change_mode(self, mode_key, overwrite=False):
        if mode_key in self._mms:
            self._last_mode = self._mode
            self._mode = mode_key
            self._print_fn("mode change to", self._mode, "last", self._last_mode)
            if overwrite:
                self._last_mode = self._mode
                self._random = False
                self._print_fn("overwrite last", self._last_mode)
                
        ##handle states
        self._drag = (self._mode == 3)  ##prioritize drag mode
        if self._drag:
            self._stationary = False
            self._random_mode = False
        else:
            if self._mode == 0:
                if not self._stationary:
                    self._stationary_ts = time.time()  ##timestamp when first changed to stationary mode
                self._stationary = True
            else:
                self._stationary = False
        ##update duration
        self._pattern_dur = 0
        
    def _set_random(self):
        self._random_mode = True
        
    def _resume_mode(self, event):
        if self._drag:  ##skip if in drag mode
            return
        self._print_fn("resume last mode", self._last_mode)
        return self._change_mode(self._last_mode)
        
    def _change_gif(self, event, num=1):
        if self._drag:  ##skip if in drag mode
            return
        self._gif_key_id = (self._gif_key_id + num)%len(self._gif_dict)  ##increment by one, round down to dict length
        key = list(self._gif_dict.keys())[self._gif_key_id]
        if key in self._gif_dict:
            self._gif = self._gif_dict[key]
            self._frame_num = len(self._gif)
            self._img = self._gif[0]
            self._print_fn("change gif", self._gif_key_id)
            
    def _menu_popup(self, event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

if __name__ == "__main__":
    src = resource_path("src")
    gif_src = []
    for f in os.listdir(src):
        if f.lower().endswith(".gif"):
            gif_src.append(os.path.join(src, f))
#    Window(gif_src="src/baby_flower.gif")
    Window(gif_src=gif_src, print_fn=None)
    sys.exit()

