"""
    This class defines the Frame for the input of the user defined functions

    Luca Lombardi
    24 May 2025: First Draft

    next steps:
     - prepare a right click menu
     - delete selected records
     - import Excel, csv or txt file

"""
from tkinter import Tk, Frame, LabelFrame, Label, StringVar, Button, Entry, Menu, Toplevel, BooleanVar
from tkinter.ttk import Combobox, Treeview, Scrollbar
from .import_excel_data import ExcelImporterApp
from TNSolver_GUI.Thermal_Network_TAB.gUtility import (unit_dict, font, font_size, validate_real_number, is_float,
                                                       validate_string)


class BasicSettings(Frame):
    def __init__(self, parent, variation_callback):
        Frame.__init__(self, parent)
        self.change_released = BooleanVar(value=False)
        self.excel_data = None
        self.import_window = None
        self.right_menu = None
        self._basic_setting_frame = LabelFrame(self, text="Basic Settings", padx=10, pady=10)
        self._basic_setting_frame.pack(side='left', pady=10, expand=True, fill='x', anchor='n')
        self.change_released.trace_add("write", variation_callback)
        # definition of the dictionary of the data, containing metadata and data array
        self.data_dict = {'name': 'no_name',
                          'data': {}}
        self.unit_list = []
        for key in unit_dict.keys():
            self.unit_list.extend(unit_dict[key][0])

        self._top_frame = Frame(self._basic_setting_frame)
        self._left_frame_top = Frame(self._top_frame)
        self._right_frame_top = Frame(self._top_frame)
        self._central_frame = Frame(self._basic_setting_frame)
        self._bottom_frame = Frame(self._basic_setting_frame)
        self._left_frame_bottom = Frame(self._bottom_frame)
        self._right_frame_bottom = Frame(self._bottom_frame)
        # --- left frame_ top ---
        self.function_name_label = Label(self._left_frame_top, text='Name', font=(font, font_size))
        self.function_name_label.pack(side='top', pady=10, anchor='w')
        self.option_label = Label(self._left_frame_top, text='Option', font=(font, font_size))
        self.option_label.pack(side='top', pady=10, anchor='w')
        self.argument_label = Label(self._left_frame_top, text='Argument Units', font=(font, font_size))
        self.argument_label.pack(side='top', pady=10, anchor='w')
        self.result_label = Label(self._left_frame_top, text='Result Units', font=(font, font_size))
        self.result_label.pack(side='top', pady=10, anchor='w')
        # --- right frame_ top ---
        self.function_name_entry = Entry(self._right_frame_top, font=(font, font_size), width=25, validate="key",
                                         validatecommand=(self.register(validate_string), "%P"))
        self.function_name_entry.pack(side='top', pady=10, anchor='w')
        self.function_name_entry.bind("<FocusOut>", lambda e: self._function_name_enter(e))
        self.function_name_entry.bind("<Return>", lambda e: self._function_name_enter(e))
        self.option_interpolator = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                            values=['Constant', 'piecewise linear', 'Monotonic Spline'])
        self.option_interpolator.pack(side='top', pady=10)
        self.argument_units = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                       values=self.unit_list)
        self.argument_units.pack(side='top', pady=10)
        self.result_units = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                     values=self.unit_list)
        self.result_units.pack(side='top', pady=10)
        # --- data_tree - _central_frame ---
        self.tree_scroll = Scrollbar(self._central_frame)
        self.tree_scroll.pack(side='right', fill='y')
        self.data_tree = Treeview(self._central_frame, height=20, yscrollcommand=self.tree_scroll.set,
                                  selectmode="extended")
        self.tree_scroll.config(command=self.data_tree.yview)
        self.data_tree['columns'] = ['Coordinate', 'Value']
        self.data_tree.column('#0', width=60)
        self.data_tree.column('Coordinate', width=110)
        self.data_tree.column('Value', width=110)
        self.data_tree.heading('#0', text='Step')
        self.data_tree.heading('Coordinate', text='Coordinate')
        self.data_tree.heading('Value', text='Value')
        self.data_tree.tag_configure('odd', background="white")
        self.data_tree.tag_configure('even', background="lightblue")
        self.data_tree.bind("<ButtonRelease-1>", self.select_record)
        # -------------------------------------------
        self.data_tree.pack(side='left')
        # --- _left_frame_bottom ---
        self.coordinate_label = Label(self._left_frame_bottom, text='Coordinate', font=(font, font_size))
        self.coordinate_label.pack(side='top', pady=10, anchor='w')
        self.value_label = Label(self._left_frame_bottom, text='Value', font=(font, font_size))
        self.value_label.pack(side='top', pady=10, anchor='w')
        self.add_button = Button(self._left_frame_bottom, text='Add', width=14, command=self.add_data)
        self.add_button.pack(side='top', pady=10, anchor='w')
        # --- _right_frame_bottom ---
        self.coordinate_data = Entry(self._right_frame_bottom, font=(font, font_size), width=18, validate="key",
                                     validatecommand=(self.register(validate_real_number), "%P"))
        self.coordinate_data.pack(side='top', pady=10, anchor='w')
        self.value_data = Entry(self._right_frame_bottom, font=(font, font_size), width=18, validate="key",
                                validatecommand=(self.register(validate_real_number), "%P"))
        self.value_data.pack(side='top', pady=10, anchor='w')
        self.remove_button = Button(self._right_frame_bottom, text='Remove', width=14, command=self.remove_data)
        self.remove_button.pack(side='top', pady=10, padx=10, anchor='w')

        self._left_frame_top.pack(side='left')
        self._right_frame_top.pack(side='left')
        self._left_frame_bottom.pack(side='left')
        self._right_frame_bottom.pack(side='left', padx=40)

        self._top_frame.pack(side='top', fill='x', pady=5, expand=True)
        self._central_frame.pack(side='top', fill='x', pady=5, expand=True)  # Ensure 'side=top'
        self._bottom_frame.pack(side='top', fill='x', pady=5, expand=True)  # Ensure 'side=top'

        self.right_menu = Menu(self._central_frame, tearoff=False)
        self.right_menu.add_command(label="Remove", command=self.remove_data)
        self.right_menu.add_command(label="Remove selection", command=self.remove_selected)
        self.right_menu.add_separator()
        self.right_menu.add_command(label="import excel file", command=self.import_excel)
        # self.right_menu.add_command(label="import csv file", command=self.import_csv)
        self.data_tree.bind("<ButtonRelease-3>", lambda event: self.right_menu_popup(event))

    def _function_name_enter(self, e):
        title = self.function_name_entry.get()
        self.data_dict['name'] = title

    def right_menu_popup(self, event):
        self.right_menu.tk_popup(event.x_root, event.y_root)

    def add_data(self):
        if is_float(self.coordinate_data.get()) and is_float(self.value_data.get()):
            coordinate = float(self.coordinate_data.get())
            value = float(self.value_data.get())
            self.data_dict['data'][coordinate] = value
            self.update_tree(self.data_dict['data'])
            self.coordinate_data.delete(0, 'end')
            self.value_data.delete(0, 'end')
        else:
            pass

    def update_tree(self, data):
        # data is a dictionary {coordinate: value}
        self.data_tree_remove_all()
        count = 1
        # create a list of ordered keys
        sorted_keys = sorted(data)
        for key in sorted_keys:
            if count % 2 == 0:
                self.data_tree.insert(parent='', index='end', text=str(count), values=(key, data[key]), tags='even')
            else:
                self.data_tree.insert(parent='', index='end', text=str(count), values=(key, data[key]), tags='odd')
            count += 1
        self.toggle_var()

    def data_tree_remove_all(self):
        for record in self.data_tree.get_children():
            self.data_tree.delete(record)

    def select_record(self, _e):
        # Clear entry boxes
        self.coordinate_data.delete(0, 'end')
        self.value_data.delete(0, 'end')

        # Grab record number
        selected = self.data_tree.focus()
        # Grab record values
        values = self.data_tree.item(selected, 'values')

        # output to entry boxes
        self.coordinate_data.insert(0, values[0])
        self.value_data.insert(0, values[1])

    def remove_data(self):
        if is_float(self.coordinate_data.get()) and is_float(self.value_data.get()):
            coordinate = float(self.coordinate_data.get())
            if coordinate in self.data_dict['data'].keys():
                del self.data_dict['data'][coordinate]
                self.update_tree(self.data_dict['data'])
                self.coordinate_data.delete(0, 'end')
                self.value_data.delete(0, 'end')
        else:
            pass

    def remove_selected(self):
        # remove selected records in the data_tree --> to be modified
        x = self.data_tree.selection()
        for record in x:
            self.data_tree.delete(record)

    def toggle_var(self):
        self.change_released.set(not self.change_released.get())  # Flip the boolean value

    def import_excel(self):
        # Create import widget
        self.import_window = Toplevel()
        self.import_window.title("Toplevel2")
        # Keep this window on top
        # self.import_window.attributes('-topmost', True)
        # to bring it to the front immediately
        self.import_window.lift()

        #   create the import excel class
        self.excel_data = ExcelImporterApp(self.import_window)
        # Create exit button
        button_close = Button(self.import_window, text="Close", command=self.close_import_window)

        self.excel_data.pack(side='top', anchor='w')
        button_close.pack(side='top', pady=10, anchor='center')

        # Display until closed manually.
        self.import_window.mainloop()

    def close_import_window(self):
        self.data_dict['data'] = {}
        self.data_dict['data'] = self.excel_data.data_dictionary
        self.update_tree(self.data_dict['data'])
        self.import_window.destroy()


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Solution Properties frame')

    function_setting_frame = BasicSettings(win, update)
    # Ensure the main frame expands and fills the root window
    function_setting_frame.pack(padx=10, pady=10, fill='both', expand=True)

    win.mainloop()
