from tkinter import Tk, LabelFrame, Label, Entry, Frame, LEFT, END, Button
from tkinter.ttk import Combobox

"""
Class Solution
It is the GUI to define the analysis type and the solver parameters

Luca Lombardi
Rev 0: First Draft

next steps:
- serialize the Solution parameters
- restart file


"""


class Analysis:
    def __init__(self):
        self.title = "Analysis title"
        self.type = "Steady State"
        self.units = 'SI'
        self.Tunits = 'C'
        self.convergence = 1e-9
        self.iterations = 1
        self.initial_temperature = 20
        self.begin_time = 0.0
        self.end_time = 1
        self.time_steps = 100
        self.print_intervals = 1
        self.StefanBoltzmann = 5.6704E-8
        self.gravity = 9.80665


class SolverSetting(Frame):
    def __init__(self, parent):
        self.analysis = Analysis
        self.initialize_all = True

        Frame.__init__(self, parent)

        labels = ['Analysis Title', 'Analysis Type', 'Unit System', 'Temperature unit', 'Convergence',
                  'max. iterations', 'Initial Temperature', 'Begin time', 'End time', 'Time steps', 'Print interval']

        self._frame_solution = LabelFrame(self, text="Solution Parameters", padx=10, pady=5, height=1100)
        self._frame_solution.pack(side='left', pady=10, expand=1, fill='x', anchor='n')

        self._left_frame = Frame(self._frame_solution)
        self._right_frame = Frame(self._frame_solution)
        self._button_frame = LabelFrame(self._frame_solution, text="Initialize nodes", padx=10, pady=10)

        self.solution_info = [None] * len(labels)

        for i, items in enumerate(labels):
            self.solution_info[i] = Label(self._left_frame, text=items)

        self.entry_list = []  # Entry list of the following widgets
        self.title_entry = Entry(self._right_frame, width=18)
        self.title_entry.insert(0, 'title')
        self.title_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.title_entry)

        self.combo_analysis = Combobox(self._right_frame, state="readonly", width=15,
                                       values=['Steady State', 'Transient'])
        self.combo_analysis.set("Steady State")
        self.combo_analysis.bind("<<ComboboxSelected>>", self.update_analysis_info)

        self.combo_unit = Combobox(self._right_frame, state="readonly", width=15,
                                   values=['SI', 'Imperial'])
        self.combo_unit.bind("<<ComboboxSelected>>", self.update_analysis_info)

        self.combo_unit.set("SI")
        self.combo_Tunit = Combobox(self._right_frame, state="readonly", width=15,
                                    values=['°C', 'K', '°F', 'R'])
        self.combo_Tunit.set("°C")
        self.combo_Tunit.bind("<<ComboboxSelected>>", self.update_analysis_info)

        self.convergence_entry = Entry(self._right_frame, width=18, validate="key",
                                       validatecommand=(self.register(self.validate_real_number), "%P"))
        self.convergence_entry.insert(0, '1e-9')
        self.convergence_entry.bind("<FocusOut>", self.update_analysis_info)
        self.convergence_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.convergence_entry)

        self.iterations_entry = Entry(self._right_frame, width=18, validate="key",
                                      validatecommand=(self.register(self.validate_integer_number), "%P"))
        self.iterations_entry.insert(0, '100')
        self.iterations_entry.bind("<FocusOut>", self.update_analysis_info)
        self.iterations_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.iterations_entry)

        self.init_temp_entry = Entry(self._right_frame, width=18, validate="key",
                                     validatecommand=(self.register(self.validate_real_number), "%P"))
        self.init_temp_entry.insert(0, '20')
        self.init_temp_entry.bind("<FocusOut>", self.update_analysis_info)
        self.init_temp_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.init_temp_entry)

        self.start_time_entry = Entry(self._right_frame, width=18, validate="key",
                                      validatecommand=(self.register(self.validate_real_number), "%P"))
        self.start_time_entry.insert(0, '0')
        self.start_time_entry.bind("<FocusOut>", self.update_analysis_info)
        self.start_time_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.start_time_entry)

        self.end_time_entry = Entry(self._right_frame, width=18, validate="key",
                                    validatecommand=(self.register(self.validate_real_number), "%P"))
        self.end_time_entry.insert(1, '1')
        self.end_time_entry.bind("<FocusOut>", self.update_analysis_info)
        self.end_time_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.end_time_entry)

        self.time_steps_entry = Entry(self._right_frame, width=18, validate="key",
                                      validatecommand=(self.register(self.validate_integer_number), "%P"))
        self.time_steps_entry.insert(0, '100')
        self.time_steps_entry.bind("<FocusOut>", self.update_analysis_info)
        self.time_steps_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.time_steps_entry)

        self.print_intervals_entry = Entry(self._right_frame, width=18, validate="key",
                                           validatecommand=(self.register(self.validate_integer_number), "%P"))
        self.print_intervals_entry.insert(0, '1')
        self.print_intervals_entry.bind("<FocusOut>", self.update_analysis_info)
        self.print_intervals_entry.bind("<Return>", self._handle_enter)
        self.entry_list.append(self.print_intervals_entry)

        self.initialize_node_button = Button(self._button_frame, text="Initial\n temperature",
                                             width=12, command=self.initialize_nodes, state='disabled')
        self.copy_solution_temp_button = Button(self._button_frame,
                                                text="Current\n solution", width=14,
                                                command=self.copy_solution, state='disabled')

        # pack the left frame
        for i in range(0, len(labels)):
            self.solution_info[i].pack(pady=5, anchor='w')

        # pack the right frame
        self.title_entry.pack(padx=5, pady=5, anchor='e')
        self.combo_analysis.pack(padx=5, pady=6, anchor='e')
        self.combo_unit.pack(padx=5, pady=5, anchor='e')
        self.combo_Tunit.pack(padx=5, pady=5, anchor='e')
        self.convergence_entry.pack(padx=5, pady=6, anchor='e')
        self.iterations_entry.pack(padx=5, pady=6, anchor='e')
        self.init_temp_entry.pack(padx=5, pady=6, anchor='e')
        self.start_time_entry.pack(padx=5, pady=6, anchor='e')
        self.end_time_entry.pack(padx=5, pady=6, anchor='e')
        self.time_steps_entry.pack(padx=5, pady=6, anchor='e')
        self.print_intervals_entry.pack(padx=5, pady=6, anchor='e')

        # Pack the buttons at the bottom of the solution frame
        self.initialize_node_button.pack(padx=0, pady=0, side='left')
        self.copy_solution_temp_button.pack(padx=5, pady=0, side='left')

        self._button_frame.pack(side='bottom', fill='x')
        self._left_frame.pack(side='left', fill='y')
        self._right_frame.pack(side='left', fill='y')

        self.combo_analysis.bind('<<ComboboxSelected>>', self.analysis_modified)
        self._frame_solution.bind('<FocusOut>', self.update_analysis_info)

        self.analysis_modified(1)

    def _handle_enter(self, event):
        """Handle Enter key press and remove focus."""
        event.widget.master.focus_set()
        self.update_analysis_info(event)

    def analysis_modified(self, event):
        if self.combo_analysis.get() == 'Transient':
            # self.iterations_entry.configure(state='normal')
            self.start_time_entry.configure(state='normal')
            self.end_time_entry.configure(state='normal')
            self.time_steps_entry.configure(state='normal')
            self.print_intervals_entry.configure(state='normal')
        else:
            # self.iterations_entry.configure(state='d')
            # self.start_time_entry.configure(state='disabled')
            self.end_time_entry.configure(state='disabled')
            self.time_steps_entry.configure(state='disabled')
            self.print_intervals_entry.configure(state='disabled')
        self.update_analysis_info(event)

    @staticmethod
    def validate_real_number(P):
        if not P:  # Empty input is always valid
            return True

        try:
            # Check for scientific notation format if "e" or "E" is present
            if "e" in P or "E" in P:
                parts = P.split("e") if "e" in P else P.split("E")
                if len(parts) > 2:
                    return False
                base, exponent = parts
                if not float(base):
                    return False
                if len(exponent) == 0 or (len(exponent) == 1 and exponent.startswith('-')):
                    return True
                elif not int(exponent):
                    return False
            elif len(P) == 1 and (P[0] == '-' or P[0] == '.' or P[0] == '+'):
                return True
            elif float(P) == 0:
                return True

            if not float(P):
                return False

            return True
        except ValueError:
            return False

    @staticmethod
    def validate_integer_number(P):
        if not P:  # Empty input is always valid
            return True
        elif P.isdigit() and int(P) >= 0:
            return True
        else:
            return False

    def update_analysis_info(self, event):
        self.analysis.title = self.title_entry.get()
        self.analysis.type = self.combo_analysis.get()
        self.analysis.units = self.combo_unit.get()
        if self.combo_Tunit.get() == '°C':
            self.analysis.Tunits = 'C'
        elif self.combo_Tunit.get() == '°F':
            self.analysis.Tunits = 'F'
        else:
            self.analysis.Tunits = self.combo_Tunit.get()
        self.analysis.convergence = self.convergence_entry.get()
        self.analysis.iterations = self.iterations_entry.get()
        self.analysis.initial_temperature = self.init_temp_entry.get()
        self.analysis.begin_time = self.start_time_entry.get()
        self.analysis.end_time = self.end_time_entry.get()
        self.analysis.time_steps = self.time_steps_entry.get()
        self.analysis.print_intervals = self.print_intervals_entry.get()
        if self.analysis.units == "SI":
            self.analysis.StefanBoltzmann = 5.6704e-8
            self.analysis.gravity = 9.80665
        else:
            self.analysis.StefanBoltzmann = 1.714e-9
            self.analysis.gravity = 32.174

    def get_analysis_setup(self):
        return self.analysis

    def serialize(self):
        serialized_solution = {"title": self.analysis.title,
                               "analysis_type": self.analysis.type,
                               "unit": self.analysis.units,
                               "temperature_unit": self.analysis.Tunits,
                               "convergence": self.analysis.convergence,
                               "iterations": self.analysis.iterations,
                               "initial_temperature": self.analysis.initial_temperature,
                               "begin_time": self.analysis.begin_time,
                               "end_time": self.analysis.end_time,
                               "time_steps": self.analysis.time_steps,
                               "print_intervals": self.analysis.print_intervals}
        return serialized_solution

    def setting_from_file(self, solution_parameter):
        for entry in self.entry_list:  # temporary enabling of the entries
            entry.config(state='normal')

        self.title_entry.delete(0, END)
        self.title_entry.insert(0, solution_parameter['title'])
        self.combo_analysis.set(solution_parameter['analysis_type'])
        self.combo_unit.set(solution_parameter['unit'])
        self.combo_Tunit.set(solution_parameter['temperature_unit'])
        self.convergence_entry.delete(0, END)
        self.convergence_entry.insert(0, solution_parameter['convergence'])
        self.iterations_entry.delete(0, END)
        self.iterations_entry.insert(0, solution_parameter['iterations'])
        self.init_temp_entry.delete(0, END)
        if 'initial_temperature' in solution_parameter:
            self.init_temp_entry.insert(0, solution_parameter['initial_temperature'])
        else:
            self.init_temp_entry.insert(0, 20.0)
        self.start_time_entry.delete(0, END)
        self.start_time_entry.insert(0, solution_parameter['begin_time'])
        self.end_time_entry.delete(0, END)
        self.end_time_entry.insert(1, solution_parameter['end_time'])
        self.time_steps_entry.delete(0, END)
        self.time_steps_entry.insert(0, solution_parameter['time_steps'])
        self.print_intervals_entry.delete(0, END)
        self.print_intervals_entry.insert(0, solution_parameter['print_intervals'])
        self.analysis_modified(1)
        self.update_analysis_info(1)

    def initialize_nodes(self):
        self.initialize_all = True

    def copy_solution(self):
        self.initialize_all = False


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Solution Properties frame')

    solution_frame = SolverSetting(win)
    solution_frame.pack(padx=10, pady=10)

    win.mainloop()
