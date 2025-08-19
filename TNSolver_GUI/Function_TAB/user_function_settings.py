"""
    This class defines the Frame for the input of the user defined functions
    Those functions are limited to time functions

    Luca Lombardi
    24 May 2025: First Draft

    next steps:
     - import csv file: a similar import ExcelImporterApp class shall be generated

"""
import numpy as np
import csv
import datetime
from tkinter import Tk, Frame, LabelFrame, Label, StringVar, Button, Entry, Menu, Toplevel, BooleanVar, messagebox
from tkinter import filedialog
from tkinter.ttk import Combobox, Treeview, Scrollbar
from .import_excel_data import ExcelImporterApp
from TNSolver_GUI.Thermal_Network_TAB.gUtility import (unit_dict, font, font_size, validate_real_number, is_float,
                                                       validate_string)


class BasicSettings(Frame):
    def __init__(self, parent, variation_callback, functions_dict, update_callback):
        Frame.__init__(self, parent)
        self.functions_dict = functions_dict
        self.update_callback = update_callback
        self.change_released = BooleanVar(value=False)
        self.excel_data = None
        self.import_window = None
        self.right_menu = None
        self._basic_setting_frame = LabelFrame(self, text="Basic Settings", padx=10, pady=10)
        self._basic_setting_frame.pack(side='left', padx=10, pady=10, expand=True, fill='x', anchor='n')
        self.change_released.trace_add("write", variation_callback)
        # definition of the dictionary of the data, containing metadata and data array
        self.data_dict = {}
        """
        This dictionary is moved into the main program and passed to the function TAB
        self.functions_dict = {'new': {'abscissa': None,
                                       'ordinate': None,
                                       'physical_property': None,
                                       'property_unit': None,
                                       'time_unit': None,
                                       'option': None}}
        """
        self._top_frame = Frame(self._basic_setting_frame)
        self._left_frame_top = Frame(self._top_frame)
        self._right_frame_top = Frame(self._top_frame)
        self._central_frame = Frame(self._basic_setting_frame)
        self._bottom_frame = Frame(self._basic_setting_frame)
        self._left_frame_bottom = Frame(self._bottom_frame)
        self._right_frame_bottom = Frame(self._bottom_frame)

        # --- left frame_ top ---
        self.function_list_label = Label(self._left_frame_top, text='Functions list', font=(font, font_size))
        self.function_list_label.pack(side='top', pady=10, anchor='w')
        self.function_name_label = Label(self._left_frame_top, text='Function name', font=(font, font_size))
        self.function_name_label.pack(side='top', pady=10, anchor='w')
        self.option_label = Label(self._left_frame_top, text='Option', font=(font, font_size))
        self.option_label.pack(side='top', pady=10, anchor='w')
        self.physic_property_label = Label(self._left_frame_top, text='Physic Property', font=(font, font_size))
        self.physic_property_label.pack(side='top', pady=10, anchor='w')
        self.property_unit_label = Label(self._left_frame_top, text='Property Unit', font=(font, font_size))
        self.property_unit_label.pack(side='top', pady=10, anchor='w')
        self.time_unit_label = Label(self._left_frame_top, text='Time Unit', font=(font, font_size))
        self.time_unit_label.pack(side='top', pady=10, anchor='w')

        # --- right frame_ top ---
        self._functions_list = list(self.functions_dict.keys())
        self.functions_list_combo = Combobox(self._right_frame_top, width=27, textvariable=StringVar(),
                                             state="readonly", values=self._functions_list)
        self.functions_list_combo.current(0)
        self.functions_list_combo.pack(side='top', pady=10)
        self.functions_list_combo.bind('<<ComboboxSelected>>', self._function_changed)

        self.function_name_entry = Entry(self._right_frame_top, font=(font, font_size), width=25, validate="key",
                                         validatecommand=(self.register(validate_string), "%P"))
        self.function_name_entry.insert(-1, 'function_1')
        self.function_name_entry.pack(side='top', pady=10, anchor='w')
        self.function_name_entry.bind("<FocusOut>", lambda e: self._function_name_enter(e))
        self.function_name_entry.bind("<Return>", lambda e: self._function_name_enter(e))

        self.option_interpolator = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                            values=['Constant', 'piecewise linear', 'Monotonic Spline'])
        self.option_interpolator.current(0)
        self.option_interpolator.pack(side='top', pady=10)

        self._physic_property_list = list(unit_dict.keys())
        self._physic_property_list.remove('time')
        self.physic_property = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                        values=self._physic_property_list)
        self.physic_property.current(0)
        self.physic_property.pack(side='top', pady=10)
        self.physic_property.bind('<<ComboboxSelected>>', self._physic_property_changed)

        self._unit_list = list(unit_dict[self.physic_property.get()][0])
        self.property_unit = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                      values=self._unit_list)
        self.property_unit.current(1)
        self.property_unit.pack(side='top', pady=10)

        self._time_unit_list = list(unit_dict['time'][0])
        self.time_unit = Combobox(self._right_frame_top, width=27, textvariable=StringVar(), state="readonly",
                                  values=self._time_unit_list)
        self.time_unit.current(1)
        self.time_unit.pack(side='top', pady=10)

        # --- data_tree - _central_frame ---
        self.tree_scroll = Scrollbar(self._central_frame)
        self.tree_scroll.pack(side='right', fill='y')
        self.data_tree = Treeview(self._central_frame, height=18, yscrollcommand=self.tree_scroll.set,
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
        self.store_button = Button(self._left_frame_bottom, text='Store function', width=14, state='disabled',
                                   command=self.store_function)
        self.store_button.pack(side='top', pady=20, anchor='w')

        # --- _right_frame_bottom ---
        self.coordinate_data = Entry(self._right_frame_bottom, font=(font, font_size), width=18, validate="key",
                                     validatecommand=(self.register(validate_real_number), "%P"))
        self.coordinate_data.pack(side='top', pady=10, anchor='w')
        self.value_data = Entry(self._right_frame_bottom, font=(font, font_size), width=18, validate="key",
                                validatecommand=(self.register(validate_real_number), "%P"))
        self.value_data.pack(side='top', pady=10, anchor='w')
        self.remove_button = Button(self._right_frame_bottom, text='Remove', width=14, command=self.remove_data)
        self.remove_button.pack(side='top', pady=10, padx=10, anchor='w')
        self.delete_button = Button(self._right_frame_bottom, text='Delete', width=14, state='disabled',
                                    command=self.delete_function)
        self.delete_button.pack(side='top', pady=20, padx=10, anchor='w')

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
        self.right_menu.add_command(label="clear all", command=self.clear_all_data)
        self.right_menu.add_separator()
        self.right_menu.add_command(label="import excel file", command=self.import_excel)
        # self.right_menu.add_command(label="import csv file", command=self.import_csv)
        self.right_menu.add_separator()
        self.right_menu.add_command(label="export csv file", command=self.export_csv)

        self.data_tree.bind("<ButtonRelease-3>", lambda event: self.right_menu_popup(event))

    def _function_changed(self, _e):
        # this function manage the change in the function list combobox
        name = self.function_name_entry.get()
        data_list = sorted([[x, y] for x, y in self.data_dict.items()])
        data_list = np.array(data_list)
        overwrite = True
        # Check if the data present at screen need to be saved...
        # ... 1st check if the name function exists...
        if name in self.functions_dict.keys():
            # ... check if the current data are matching the stored function...
            # ... check for size first...
            if len(self.functions_dict[name]['abscissa']) == len(data_list[:, 0]):
                # ... then check for content
                if ((self.functions_dict[name]['abscissa'] == data_list[:, 0]).all() and
                        (self.functions_dict[name]['ordinate'] == data_list[:, 1]).all() and
                        self.functions_dict[name]['physic_property'] == self.physic_property.get() and
                        self.functions_dict[name]['physic_unit'] == self.property_unit.get() and
                        self.functions_dict[name]['time_unit'] == self.time_unit.get() and
                        self.functions_dict[name]['option'] == self.option_interpolator.get()):
                    overwrite = False
            if overwrite:
                # the current function has been modified and not saved, ask if it needs to be saved first
                _message = "The function has been modified, do you want to overwrite the data?"
                check = messagebox.askyesno(title="Function changed", message=_message)
                if not check:
                    overwrite = False
        else:
            # ...the current function is new and not saved, ask if it needs to be saved first
            _message = "The function is not stored, do you want to save the data first?"
            check = messagebox.askyesno(title="Save the function", message=_message)
            if not check:
                overwrite = False

        # final control for saving or not the data in the data tree.
        if overwrite:
            self._archive(name)

        # check completed, next action is to check if it is requested to describe a new function or plot an existing one
        if self.functions_list_combo.get() == 'new':
            self.function_name_entry.delete(0, 'end')
            self.clear_all_data()
            self.data_dict = {}
            self.toggle_var()
        else:
            # a stored function has been called
            self.clear_all_data()
            self.data_dict = {}
            self.function_name_entry.delete(0, 'end')
            name = self.functions_list_combo.get()
            self.function_name_entry.insert(-1, name)
            for i in range(len(self.functions_dict[name]['abscissa'])):
                self.data_dict[self.functions_dict[name]['abscissa'][i]] = self.functions_dict[name]['ordinate'][i]
            self.update_tree()
            self.toggle_var()

    def _physic_property_changed(self, _e):
        # this function is triggered by the change in the physic property changed
        self._unit_list = list(unit_dict[self.physic_property.get()][0])
        self.property_unit['values'] = self._unit_list
        self.property_unit.current(0)

    def store_function(self):
        # this function slice copy the data into the functions dictionary
        name = self.function_name_entry.get()
        if len(name) == 0:
            messagebox.showerror(title='Storing error', message='The function name is missing')
            return
        overwrite = True
        data_list = sorted([[x, y] for x, y in self.data_dict.items()])
        data_list = np.array(data_list)
        # Check if the current function exists.
        if name in self.functions_dict.keys():
            # 2 check if the current data are matching the stored function...
            # ... check for size first...
            if len(self.functions_dict[name]['abscissa']) == len(data_list[:, 0]):
                # ... then check for content
                if ((self.functions_dict[name]['abscissa'] == data_list[:, 0]).all() and
                        (self.functions_dict[name]['ordinate'] == data_list[:, 1]).all() and
                        self.functions_dict[name]['physic_property'] == self.physic_property.get() and
                        self.functions_dict[name]['physic_unit'] == self.property_unit.get() and
                        self.functions_dict[name]['time_unit'] == self.time_unit.get() and
                        self.functions_dict[name]['option'] == self.option_interpolator.get()):
                    overwrite = False

            if overwrite:
                # the current function has been modified and not saved, ask if it needs to be saved first
                _message = "The function has been modified, do you want to overwrite the data?"
                check = messagebox.askyesno(title="Function changed", message=_message)
                if check:
                    self._archive(name)
                else:
                    return
            else:
                return
        else:
            # the current function is new and not saved, prepare the dictionary
            self.functions_dict[name] = {}
            self._archive(name)

    def _archive(self, name):
        data_list = sorted([[x, y] for x, y in self.data_dict.items()])
        data_list = np.array(data_list)
        self.functions_dict[name]['abscissa'] = data_list[:, 0]
        self.functions_dict[name]['ordinate'] = data_list[:, 1]
        self.functions_dict[name]['physic_property'] = self.physic_property.get()
        self.functions_dict[name]['physic_unit'] = self.property_unit.get()
        self.functions_dict[name]['time_unit'] = self.time_unit.get()
        self.functions_dict[name]['option'] = self.option_interpolator.get()

        self._functions_list = list(self.functions_dict.keys())
        self.functions_list_combo['values'] = self._functions_list
        idx = self._functions_list.index(name)
        self.functions_list_combo.current(idx)

        self.coordinate_data.delete(0, 'end')
        self.value_data.delete(0, 'end')
        # Inform the parent that function dictionary has changed
        self.update_callback()

    def delete_function(self):
        pass

    def _function_name_enter(self, e):
        pass
        # title = self.function_name_entry.get()
        # self.data_dict['name'] = title

    def right_menu_popup(self, event):
        self.right_menu.tk_popup(event.x_root, event.y_root)

    def add_data(self):
        if is_float(self.coordinate_data.get()) and is_float(self.value_data.get()):
            coordinate = float(self.coordinate_data.get())
            value = float(self.value_data.get())
            self.data_dict[coordinate] = value
            self.update_tree()
            self.coordinate_data.delete(0, 'end')
            self.value_data.delete(0, 'end')
        else:
            pass

    def update_tree(self):
        # data is a dictionary {coordinate: value}
        self.data_tree_remove_all()
        count = 1
        # create a list of ordered keys
        for key in sorted(self.data_dict):
            if count % 2 == 0:
                self.data_tree.insert(parent='', index='end', text=str(count),
                                      values=(key, self.data_dict[key]), tags='even')
            else:
                self.data_tree.insert(parent='', index='end', text=str(count),
                                      values=(key, self.data_dict[key]), tags='odd')
            count += 1
        if count == 1:  # means the dictionary is empty
            self.store_button.config(state='disabled')
            self.delete_button.config(state='disabled')
        else:
            self.store_button.config(state='normal')
            self.delete_button.config(state='normal')
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
            if coordinate in self.data_dict.keys():
                del self.data_dict[coordinate]
                self.update_tree()
                self.coordinate_data.delete(0, 'end')
                self.value_data.delete(0, 'end')
        else:
            pass

    def remove_selected(self):
        # remove selected records in the data_tree --> to be modified
        x = self.data_tree.selection()
        for record in x:
            self.data_tree.delete(record)

    def clear_all_data(self):
        self.data_tree_remove_all()
        self.coordinate_data.delete(0, 'end')
        self.value_data.delete(0, 'end')
        self.store_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.toggle_var()

    def toggle_var(self):
        self.change_released.set(not self.change_released.get())  # Flip the boolean value

    def import_excel(self):
        # Create import widget
        self.import_window = Toplevel()
        self.import_window.title("Toplevel2")
        # Keep this window on top
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

    def export_csv(self):
        """
        Opens a file dialog for the user to save a CSV file
        and writes the provided data to it.
        """
        name = self.function_name_entry.get()
        physic_property = self.physic_property.get()
        property_unit = self.property_unit.get()
        time_unit = self.time_unit.get()
        current_date = datetime.datetime.now()
        if len(self.data_dict) == 0:
            return
        if len(physic_property) == 0 or len(property_unit) == 0:
            messagebox.showerror(title='Incomplete function', message='Check the missing info!')

        data_list = sorted([[x, y] for x, y in self.data_dict.items()])
        data_list = np.array(data_list)
        # Prompt the user for a file name and location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save your data as a CSV file")

        # If the user cancels the dialog, the file_path will be an empty string
        if file_path:
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)

                # Write a header row
                writer.writerow(["TNSolver GUI"])
                writer.writerow(["Function saved on: " + current_date.strftime("%Y-%B-%d %H:%M:%S")])
                writer.writerow(["Function name: " + name])
                writer.writerow(["-------------------------"])
                writer.writerow(["Time", physic_property])
                writer.writerow(['[' + time_unit + ']',  '[' + property_unit + ']'])
                # Write the data rows
                writer.writerows(data_list)

            messagebox.showinfo("Success", f"Data successfully exported to {file_path}")
        else:
            print("Export operation cancelled.")

    def close_import_window(self):
        self.data_dict = {}
        self.data_dict = self.excel_data.data_dictionary
        self.update_tree()
        self.import_window.destroy()


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Solution Properties frame')

    function_setting_frame = BasicSettings(win, update)
    # Ensure the main frame expands and fills the root window
    function_setting_frame.pack(padx=10, pady=10, fill='both', expand=True)

    win.mainloop()
