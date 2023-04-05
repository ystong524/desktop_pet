##ref: https://seebass22.github.io/python-desktop-pet-tutorial/2021/05/16/desktop-pet.html
import tkinter as tk
import time
import random
from win32api import GetSystemMetrics, GetMonitorInfo, MonitorFromPoint

def get_win_geometry(exclude_taskbar=False):
    if exclude_taskbar:
        monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
        work_area = monitor_info.get("Work")
        return work_area[2], work_area[3]
    else:
        return GetSystemMetrics(0), GetSystemMetrics(1)

class Window(object):
    def __init__(self, img, gif=None, exclude_taskbar=True, lim_w=30, lim_h=30):
        ##init window
        self._window = tk.Tk()
        self._window.config(highlightbackground="black")  ##set focushighlight black when not focused
        self._window.overrideredirect(True)  ##make frameless
        self._window.attributes("-topmost", True)  ##top level
        self._window.wm_attributes("-transparentcolor", "black")  ##turn black into transparent
        
        ##arguments
        self._img = tk.PhotoImage(file=img)
        self._gif = gif
        self._exclude_taskbar = exclude_taskbar
        self._lim_w = lim_w
        self._lim_h = lim_h
        
        ##internal variables
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
        
        ## count gif frames
        if not self._gif is None:
            frame_num = 0
            while True:
                try:
                    temp = tk.PhotoImage(file=gif, format="gif -index {}".format(frame_num))
                except Exception as e:
                    break
                else:
                    frame_num += 1
            assert frame_num > 0, "GIF has no frames"
            self._frame_num = frame_num
            self._gif = [tk.PhotoImage(file=gif, format="gif -index {}".format(i)) for i in range(self._frame_num)]
            self._img = self._gif[self._frame_id]
        else:
            self._gif = [self._img]
        
        ##image label
        self._label = tk.Label(self._window, bd=0, bg="black")
        
        ##geometry and display label
        self._update_win_label()

        ##mainloop
        self._time = time.time()  ##update time now
        while not(self._x_incre or self._y_incre):
            self._moving_pattern()  ##first pattern
        self._window.after(0, self._update)  ##run ._update now to start the recursive loop
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
            def randomize():
                direct = random.choice([-1, 0, 1])
                step = random.randrange(1, 10)
                return direct * step
            self._x_incre = randomize()
            self._y_incre = randomize()
            self._pattern_dur = round(random.random() * 10, 2)
        self._pattern_time = time.time()
        print(self._pattern_dur, self._x_incre, self._y_incre)
        

if __name__ == "__main__":
    Window(img="src/connection_green.png", gif="src/disco_duck.gif")

