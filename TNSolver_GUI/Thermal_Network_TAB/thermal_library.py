from tkinter import Tk, LabelFrame, Label, Scale, Frame, Button, END
from tkinter.ttk import Treeview


class ThermalLibrary(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.text = None
        self._frame_thlib = LabelFrame(self, text="Thermal Element Library", height=450, padx=10, pady=5)
        self._frame_thlib.grid_propagate(True)
        self._frame_thlib.pack(side='left', pady=10, expand=1, fill='x', anchor='n')

        self.thermal_elm = Treeview(self._frame_thlib, height=20, selectmode='browse', show='tree')
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Internal Node")
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Boundary Conditions")
        self.thermal_elm.insert(self.item, END, text="Temperature")
        self.thermal_elm.insert(self.item, END, text="Heat Flux")
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Conduction")
        self.thermal_elm.insert(self.item, END, text="Linear conduction")
        self.thermal_elm.insert(self.item, END, text="Cylindrical conduction")
        self.thermal_elm.insert(self.item, END, text="Spherical conduction")
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Convection")
        self.thermal_elm.insert(self.item, END, text="assigned HTC")
        self.subitem = self.thermal_elm.insert(self.item, END, text="Internal Forced Convection")
        self.thermal_elm.insert(self.subitem, END, text="pipe/duct")
        # -------------------------------------------
        self.subitem = self.thermal_elm.insert(self.item, END, text="External Forced Convection")
        self.thermal_elm.insert(self.subitem, END, text="Cylinder")
        self.thermal_elm.insert(self.subitem, END, text="Diamond/Square")
        self.thermal_elm.insert(self.subitem, END, text="Impinging Round jet")
        self.thermal_elm.insert(self.subitem, END, text="Flat Plate")
        self.thermal_elm.insert(self.subitem, END, text="EFC Sphere")
        # -------------------------------------------
        self.subitem = self.thermal_elm.insert(self.item, END, text="Internal Natural Convection")
        self.thermal_elm.insert(self.subitem, END, text="Vertical rectangular enclosure")
        # -------------------------------------------
        self.subitem = self.thermal_elm.insert(self.item, END, text="External Natural Convection")
        self.thermal_elm.insert(self.subitem, END, text="ENC Horizontal cylinder")
        self.thermal_elm.insert(self.subitem, END, text="Horizontal plate facing down")
        self.thermal_elm.insert(self.subitem, END, text="Horizontal plate facing up")
        self.thermal_elm.insert(self.subitem, END, text="Inclined plate facing down")
        self.thermal_elm.insert(self.subitem, END, text="Inclined plate facing up")
        self.thermal_elm.insert(self.subitem, END, text="ENC Sphere")
        self.thermal_elm.insert(self.subitem, END, text="Vertical flat plate")
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Radiation")
        self.thermal_elm.insert(self.item, END, text="Surface Radiation")
        self.thermal_elm.insert(self.item, END, text="Radiation")
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Advection")
        self.thermal_elm.insert(self.item, END, text="Advection")
        self.thermal_elm.insert(self.item, END, text="Outflow")
        # -------------------------------------------
        self.item = self.thermal_elm.insert("", END, text="Sources")
        self.thermal_elm.insert(self.item, END, text="Volumetric heat source")
        self.thermal_elm.insert(self.item, END, text="Total Heat source")
        self.thermal_elm.insert(self.item, END, text="Thermostatic heat source")

        self.thermal_elm.pack(side='left', pady=10, expand=1, fill='x', anchor='nw')

    def get_thermal_elm(self):
        if self.thermal_elm.selection()[0]:
            # explore the treeview widget and collect the parents
            item = self.thermal_elm.selection()[0]
            item_txt = [self.thermal_elm.item(item, option="text")]
            parent = self.thermal_elm.parent(item)
            while parent:
                item_txt.append(self.thermal_elm.item(parent, option="text"))
                parent = self.thermal_elm.parent(parent)
            return item_txt
        else:
            pass

    def is_leaf(self):
        if self.thermal_elm.selection()[0]:
            item = self.thermal_elm.selection()[0]
            if self.thermal_elm.get_children(item):
                return False
            else:
                return True
        else:
            pass


def main():
    def show_selected(event):
        item = th_elm.get_thermal_elm()
        a["text"] = "Element selected: " + item[0]
        b["text"] = "Ancestor: " + item[-1]
        leaf = th_elm.is_leaf()
        if leaf:
            c["text"] = "Is it a Leaf?: True!"
        else:
            c["text"] = "Is it a Leaf?: False!"

    win = Tk()
    win.title('Test of treeview')

    th_elm = ThermalLibrary(win)
    th_elm.grid(row=1, column=1)

    a = Label(win, text="Element selected:")
    a.grid(row=2, column=1)

    b = Label(win, text="Parent item:")
    b.grid(row=3, column=1)

    c = Label(win, text="Is it a Leaf?:")
    c.grid(row=4, column=1)

    th_elm.thermal_elm.bind("<ButtonRelease-1>", show_selected)

    win.mainloop()


if __name__ == '__main__':
    main()

