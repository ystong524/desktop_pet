##ref: https://seebass22.github.io/python-desktop-pet-tutorial/2021/05/16/desktop-pet.html
import tkinter as tk
import time
import random
from win32api import GetSystemMetrics, GetMonitorInfo, MonitorFromPoint
import os
import sys

##https://stackoverflow.com/a/60953781
def resource_path(path_name):
    """ return absolute path for resources located at relative
        to the directory of this script or sys._MEIPASS"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, path_name)


""" ----- window size ------- """
def get_win_geometry(exclude_taskbar=False):
    if exclude_taskbar:
        monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
        work_area = monitor_info.get("Work")
        return work_area[2], work_area[3]
    else:
        return GetSystemMetrics(0), GetSystemMetrics(1)


""" ----- motion pattern ------- """
def random_motion(x_lower=1, x_upper=10, y_lower=1, y_upper=10):
    ##random for both x and y
    return random_direct_step(lower=x_lower, upper=x_upper),\
           random_direct_step(lower=y_lower, upper=y_upper)

def random_direct_step(lower=1, upper=10):
    """
    return a numerical value symbolizing
    direction (backward-, stationery 0, forward +) and steps to be taken
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

def stop():
    return 0, 0

""" ----- gif source ------- """
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

class Window(object):
    def __init__(self, img_src=None, gif_src=None, exclude_taskbar=True, lim_w=30, lim_h=30):
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
        
        ##internal variables
        self._img = None
        self._gif = None
        self._win_w, self._win_h = get_win_geometry(exclude_taskbar=self._exclude_taskbar)
        self._frame_num = 1
        self._frame_id = 0
        self._pattern_time = time.time()
        self._pattern_dur = round(random.random() * 10, 2)
        self._time = time.time()
        self._x = random.randrange(0, self._win_w)
        self._y = random.randrange(0, self._win_h)
        self._x_incre = 0
        self._y_incre = 0
        self._mode = 0
        self._mms = {0: random_small, 1: random_large, 2: stop}
        self._gif_dict = {}
        self._key = 0
        
        
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
                            print("WARNING: {} not found".format(path))
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
        
        self._frame_num = len(self._gif)
        
        ##check img file
        assert not (self._img is None), "Image / GIF file failed to load"
        
        ##image label
        self._label = tk.Label(self._window, bd=0, bg="black")
        
        ##geometry and display label
        self._update_win_label()
        
        ##menu
        ##https://www.geeksforgeeks.org/right-click-menu-using-tkinter/
        self._menu = tk.Menu(self._window, tearoff=0)
        self._menu.add_command(label="Exit", command=self._window.destroy)
        
        ##event bind
        self._window.bind("<Button-1>", self._change_gif)
        self._window.bind("<Enter>", self._change_stop)
        self._window.bind("<Leave>", self._change_start)
        self._window.bind("<Button-3>", self._menu_popup)
        
        ##mainloop
        self._time = time.time()  ##update time now
        while not(self._x_incre or self._y_incre):
            self._moving_pattern()  ##first pattern
        self._window.after(0, self._update)  ##run ._update now to start the recursive loop
        
        #self._window.withdraw()
        #self._window.deiconify()
        self._window.protocol("WM_DELETE_WINDOW", self._window.iconify)
        self._window.mainloop()  ##start window loop here
    
    def _update_win_label(self):
        ##ensure within screen boundaries  ##allow exceeding at some limits/change motion
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
                                                       x=self._x, y=self._y))
        self._label.configure(image=self._img)
        self._label.pack()
        
    def _update_image(self, zoom=True, scale=1):
        self._frame_id = (self._frame_id + 1) % self._frame_num
        if scale != 1:
            if zoom:
                self._img = self._gif[self._frame_id].zoom(scale, scale)
            else:
                self._img = self._gif[self._frame_id].subsample(scale, scale)
        else:
            self._img = self._gif[self._frame_id]
        
    def _update(self):
        ##motion pattern
        if (time.time() - self._pattern_time) > self._pattern_dur:
            self._moving_pattern()
            
        ##update
        if (time.time() - self._time) > 0.05:  ##TODO: skip addition every loop, instead add on the _time
            self._time = time.time()  ##TODO: refresh time first or frame
            ##update steps
            self._x += self._x_incre
            self._y += self._y_incre
            ##update to image (frame & scale control)
            self._update_image(zoom=True, scale=1)
            
            ## update window and label (boundary control)
            self._update_win_label()
        
        ##execute update
        self._window.after(10, self._update)  ##call ._update recursively
    
    def _moving_pattern(self):
        if random.choice([0, 1]):
            self._x_incre, self._y_incre = self._mms[self._mode]()
            if self._x_incre or self._y_incre:
                self._pattern_dur = round(random.random() * 10, 2)
            else:
                self._pattern_dur = 1
        self._pattern_time = time.time()
#        print(self._pattern_dur, self._x_incre, self._y_incre)
    
    def _change_mode(self, event):
        if self._mode == 0:
            self._mode = 1
        else:
            self._mode = 0
        self._pattern_dur = 0
#        print("mode change to ", self._mode)
        
    def _change_stop(self, event):
        self._mode = 2
        self._pattern_dur = 0
        self._pattern_dur = 0
#        print("stop ", self._mode)
        
    def _change_start(self, event):
        self._mode = 0
        self._pattern_dur = 0
#        print("start ", self._mode)
        
    def _change_gif(self, event):
        self._key += 1
        key = self._key%len(self._gif_dict)
        if key in self._gif_dict:
            self._gif = self._gif_dict[key]
            self._frame_num = len(self._gif)
            self._img = self._gif[0]
#            print("change gif", self._key)

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
#    print(gif_src)
#    Window(gif_src="src/baby_flower.gif")
    Window(gif_src=gif_src)
#    print("exit")
    sys.exit()

