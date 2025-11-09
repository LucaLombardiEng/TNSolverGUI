"""
    Class UserFunctionFrame
    This GUI TAB permits the definition of the user defined functions by points

    Luca Lombardi
    29 May 2025: First Draft

    next steps:
     -


"""

from tkinter import Tk, Frame, PanedWindow
from tkinter.font import Font
import numpy as np

from .user_function_settings import BasicSettings
from .data_graphic_interface import FunctionPlotter


class UserFunctionDefinition(Frame):
    def __init__(self, parent, functions_dict, update_callback):
        Frame.__init__(self, parent)
        # initialize variables
        self.functions_dict = functions_dict
        self.update_callback = update_callback
        self.main_panned_window = PanedWindow(self, orient='horizontal')
        self.left_panned_window = PanedWindow(self.main_panned_window, orient='horizontal')
        self.right_panned_window = PanedWindow(self.main_panned_window, orient='horizontal')

        self.data_frame = BasicSettings(self.left_panned_window, self.data_variation, self.functions_dict,
                                        self.update_callback)
        self.plot_frame = FunctionPlotter(self.right_panned_window)

        self.main_panned_window.pack(fill='both', expand=1)
        self.main_panned_window.add(self.left_panned_window, sticky='nw', stretch='always')
        self.left_panned_window.add(self.data_frame, sticky='nw', stretch='always')
        self.main_panned_window.add(self.right_panned_window, sticky='nw', stretch='always')
        self.right_panned_window.add(self.plot_frame, padx=10, sticky='nw', stretch='last')

    def data_variation(self, var_name, index, mode):
        """something is changed in the data tree, the graph can be updated"""
        data_dict = self.data_frame.data_dict
        data = np.array(list(data_dict.items()))
        self.plot_frame.x_label = self.data_frame.physic_property.get()
        self.plot_frame.y_label = self.data_frame.property_unit.get()
        self.plot_frame.title = self.data_frame.function_name_entry.get()
        self.plot_frame.plot_function(data)

    def refresh_display(self):
        self.data_frame.refresh_function_list()


if __name__ == "__main__":
    win = Tk()
    win.title('Test of the user function definition')

    tab = UserFunctionDefinition(win)
    tab.pack(padx=10, pady=10, fill='both', expand=True)
    tab.plot_frame.default_function()

    win.mainloop()
