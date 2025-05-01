"""
    Class TimeSlider
    This class permits to scroll the solutions of a transient run.

    Luca Lombardi
    Rev 0: First Draft

    next steps:
    ...
"""

from tkinter import Tk, LabelFrame, Label, Scale, Frame


class ScaleFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self._unit = None
        self._scale_title = "Scale name"
        self._frame_scale = LabelFrame(self, text=self._scale_title, height=110, width=160, padx=5)
        self._frame_scale.pack(side='left', expand=1, fill='x')

        self.scale = Scale(self._frame_scale, from_=1, to=16, length=300, tickinterval=5, orient='horizontal',
                           resolution=0.1, sliderlength=15)
        self.scale.set(6.3)
        self.scale.pack(padx=5, side='left', fill='x')
        self.scale_active = False

        self._scale_unit = Label(self._frame_scale, text="s", width=1)
        self._scale_unit.pack(side='left', fill='x')

    def scale_title(self, _scale_title: str = "Scale Title"):
        self._scale_title = _scale_title
        self._frame_scale.configure(text=self._scale_title)

    def scale_unit(self, _unit: str = "s"):
        self._unit = _unit
        self._scale_unit["text"] = self._unit

    def scale_configure(self, s):
        """
        setting is a list [from, to, time steps, time]
        """
        setting = [float(i) for i in s]
        interval = (setting[1]-setting[0])/5.
        resolution = (setting[1]-setting[0])/setting[2]
        self.scale.configure(from_=setting[0], to=setting[1], tickinterval=interval, resolution=resolution)
        self.scale.set(setting[3])

    def get_value(self):
        return float(self.scale.get())

    def disable(self):
        self._frame_scale.config(fg="gray")
        self.scale_active = False
        for self.child in self._frame_scale.winfo_children():
            self.child.configure(state='disable', fg="gray")

    def enable(self):
        self._frame_scale.config(fg="black")
        self.scale_active = True
        for self.child in self._frame_scale.winfo_children():
            self.child.configure(state='active', fg="black")


if __name__ == "__main__":
    root = Tk()

    slider = ScaleFrame(root)
    slider.scale_unit("s")
    slider.scale_title("time steps")
    slider.scale.configure(from_=0, to=15, tickinterval=5, resolution=0.25)
    slider.scale.set(8.5)
    slider.pack()
    root.mainloop()