"""
    Main GUI for the TNSolver
    It is the GUI that permits the generation and manipulation of the TNSolver inputs.

    Luca Lombardi
    Rev 0: First Draft

    next steps:
        - add the background to the saved database
        - rebuild the background from the database

        TABS
        - create the user function tab
        - create the user material tab
        - create the user enclosure tab
        - create the user correlation tab
        - create the user init cond tab
        - create the converge tab

        Help/About
        - add link to GIT hub
        - add license
        - add link to libraries used
        - add link to original TNSolver GIT Hub
"""
import pickle
import os
from tkinter import Tk, Menu, Toplevel, Label, Button, Frame
from tkinter import filedialog, messagebox
from tkinter.ttk import Notebook, Sizegrip
from PIL import ImageTk, Image

from TNSolver_GUI.Thermal_Network_TAB import gUtility
from TNSolver_GUI.Thermal_Network_TAB.thermal_network_main import ThermalNetwork
from TNSolver_GUI.Thermal_Network_TAB.create_input_file import TNSolver_input_file_gen
from TNSolver_GUI.Thermal_Network_TAB.dxf_viewer import DXFViewer
from TNSolver_code.core_solver import tn_solver
from TNSolver_GUI.Function_TAB.tabular_user_function_main import UserFunctionDefinition


def win_about():
    revision = "1.0.0"
    mail = "luca.lombardi.ing@gmail.com"

    win = Toplevel(root, background="white", borderwidth=2)
    win.iconbitmap('./Pictures/icon_TNS.ico')
    win.wm_title("About...")

    def win_exit():
        win.destroy()
        win.quit()

    title = Label(win, text="About TNSolver GUI", bg="black", fg="green", justify="center")
    title.config(font=("Helvetica", 18))
    title.grid(row=1, column=1, columnspan=2, sticky="ew")

    img_TNS = Image.open("Pictures/TNS_logo.png").resize((382, 300), Image.Resampling.BICUBIC)
    img_TNS = ImageTk.PhotoImage(img_TNS)
    left_label = Label(win, image=img_TNS, bg="white")
    left_label.grid(row=2, column=1)

    info_text = Label(win, text="TNSolver GUI {}\nCreated by Luca Lombardi\n"
                                "For info contact the author at\n{}".format(revision, mail),
                      wraplength=300, justify='left', bg="white", font=("Helvetica", 12))
    info_text.grid(row=2, column=2, sticky="nsew")

    quit_button = Button(win, text="Quit", command=win_exit)
    quit_button.grid(row=3, column=1, columnspan=2, pady=10)

    win.mainloop()


class MainApplication(Frame):

    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        # Centralized Data Store. This dictionary will hold all function definitions
        self.functions_dict = {'new': {'abscissa': None,
                                       'ordinate': None,
                                       'physic_property': None,
                                       'property_unit': None,
                                       'time_unit': None,
                                       'option': None}}
        self.thermal_network_tab = None
        self.user_function_tab = None
        self.user_material_tab = None
        self.user_enclosure_tab = None
        self.user_correlation_tab = None
        self.user_init_cond_tab = None
        self.converge_tab = None
        self.tab_ctrl = Notebook(parent)
        self.setup_menubar(parent)
        self.setup_notebook()
        self.working_folder = None
        self.filename = None
        self.solver_input_file = None
        self.background_folder = None
        self.background_filename = None

    def setup_menubar(self, root):
        menubar = Menu(root)
        menu_file = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="New", command=self.new_network)
        menu_file.add_command(label="Open", command=self.load_network)
        menu_file.add_command(label="Save", command=self.save_network)
        menu_file.add_command(label="Save As", command=self.save_as_network)
        menu_file.add_command(label="Close", command=self.close)
        menu_file.add_separator()
        menu_file.add_command(label="Import DXF", command=self.import_DXF)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.quit)

        menu_simulate = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulate", menu=menu_simulate)
        menu_simulate.add_command(label="Export input file", command=self.generate_input_file)
        menu_simulate.add_separator()
        menu_simulate.add_command(label="Run", command=self.run_solver)

        menu_help = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=menu_help)
        menu_help.add_command(label="About...", command=win_about)

        root.config(menu=menubar)

    def do_nothing(self):
        pass

    def setup_notebook(self):
        self.thermal_network_tab = ThermalNetwork(self.tab_ctrl, self.functions_dict)
        # Create the tabs, passing the data store and update method
        self.user_function_tab = UserFunctionDefinition(self.tab_ctrl, self.functions_dict,
                                                        self.update_function_callback)
        self.user_material_tab = Frame(self.tab_ctrl)
        self.user_enclosure_tab = Frame(self.tab_ctrl)
        self.user_correlation_tab = Frame(self.tab_ctrl)
        self.user_init_cond_tab = Frame(self.tab_ctrl)
        self.converge_tab = Frame(self.tab_ctrl)

        self.tab_ctrl.add(self.thermal_network_tab, text="Thermal network")
        self.tab_ctrl.add(self.user_function_tab, text="Functions")
        self.tab_ctrl.add(self.user_material_tab, text="Materials")
        self.tab_ctrl.add(self.user_enclosure_tab, text="Enclosures")
        self.tab_ctrl.add(self.user_correlation_tab, text="Correlations")
        self.tab_ctrl.add(self.user_init_cond_tab, text="Initial conditions")
        self.tab_ctrl.add(self.converge_tab, text="Convergence")

        self.tab_ctrl.pack(expand=1, fill="both")

    def update_function_callback(self):
        """
        This is the central method that user_function_tab calls to trigger an update.
        It then calls the specific update method on thermal_network_tab.
        """
        self.thermal_network_tab.update_functions()

    def new_network(self):
        check = messagebox.askyesno(title="Create a new Network", message="Do you want to create a new network?")
        if check:
            self.thermal_network_tab.network_reset()
            self.functions_dict.clear()
            self.functions_dict['new'] = {'abscissa': None,
                                          'ordinate': None,
                                          'physic_property': None,
                                          'property_unit': None,
                                          'time_unit': None,
                                          'option': None}
            self.thermal_network_tab.bottomFrame.clear_text()
            self.thermal_network_tab.welcome_message()
        else:
            self.thermal_network_tab.bottomFrame.write_text('Command aborted\n')

    def load_network(self):
        # check if a thermal network is already available
        if len(self.thermal_network_tab.node_dict) > 0:
            check = messagebox.askyesnocancel(title="Close the network",
                                              message="Do you want to save the work before proceed?")
            if check is True:
                self.save_network()
            elif check is False:
                self.thermal_network_tab.network_reset()
            elif check is None:
                return

        filename = filedialog.askopenfilename(initialdir=gUtility.working_folder_path, title="Select a File",
                                              filetypes=(("Binary file", "*.pkl"), ("all files", "*.*")))

        if filename:  # Check if a filename was actually selected
            # Extract both working directory and filename
            self.working_folder, self.filename = os.path.split(filename)

            # Handle potential empty working_dir if the user selects the root directory
            if self.working_folder:
                self.working_folder = os.path.abspath(self.working_folder)
                with open(filename, 'rb') as f:
                    serialized_data = pickle.load(f)
                f.close()

                # retrieve the Solution definition
                if 'Solution' in serialized_data:
                    self.thermal_network_tab.solution_Frame.setting_from_file(serialized_data["Solution"])
                    if serialized_data['Solution']['analysis_type'] == 'Transient':
                        self.thermal_network_tab.slider_Frame.enable()
                        from_ = serialized_data['Solution']['begin_time']
                        to_ = serialized_data['Solution']['end_time']
                        steps = serialized_data['Solution']['time_steps']
                        self.thermal_network_tab.slider_Frame.scale_configure([from_, to_, steps, to_])

                    else:
                        self.thermal_network_tab.slider_Frame.disable()
                else:
                    self.thermal_network_tab.slider_Frame.disable()

                # retrieve the Functions definitions
                if 'Functions' in serialized_data:
                    self.functions_dict.clear()  # clear the dictionary
                    self.functions_dict.update(serialized_data['Functions'])  # update the main function dictionary
                    # self.thermal_network_tab.update_functions()
                    self.thermal_network_tab.rightFrame.group_functions_by_unit()
                    self.user_function_tab.refresh_display()  # trigger the update of the fn dictionary in the fn tab
                else:
                    pass

                # retrieve the nodes and splash on the graphic area
                serialized_nodes = serialized_data["Nodes"]
                for key in serialized_nodes.keys():
                    self.thermal_network_tab.load_node(serialized_nodes[key])

                # retrieve the elements and splash on the graphic area
                serialized_elements = serialized_data["Elements"]
                for key in serialized_elements.keys():
                    self.thermal_network_tab.load_element(serialized_elements[key])

            else:
                pass

    def import_DXF(self):
        """
        # check if a DXF background is already present:
        if len(self.thermal_network_tab.node_dict) > 0:
            check = messagebox.askyesnocancel(title="Close the network",
                                              message="Do you want to save the work before proceed?")
            if check is True:
                self.save_network()
            elif check is False:
                self.thermal_network_tab.network_reset()
            elif check is None:
                return
        """
        filename = filedialog.askopenfilename(initialdir=gUtility.working_folder_path,
                                              title="Select a Drawing Exchange Forma File",
                                              filetypes=(("Binary file", "*.dxf"), ("all files", "*.*")))

        if filename:  # Check if a filename was actually selected
            # Extract both working directory and filename
            self.background_folder, self.background_filename = os.path.split(filename)

            # Handle potential empty working_dir if the user selects the root directory
            if self.background_folder:
                self.background_folder = os.path.abspath(self.background_folder)

            background = DXFViewer(self.thermal_network_tab.centralFrame.th_canvas, filename)
            segment, dimension = background.get_dimension()
            graph, _ = self.thermal_network_tab.graph_area()
            x = ((graph[1] - graph[0]) - segment) / 2
            y = graph[3] - 150
            background.draw_meter_scale(x, y, segment, dimension, 'mm')

    def save_network(self):
        if self.filename is None:
            self.save_as_network()
        else:
            self.save()

    def save_as_network(self):
        filename = filedialog.asksaveasfilename(initialdir=gUtility.working_folder_path, title="Select a File",
                                                filetypes=(("Binary file", "*.pkl"), ("all files", "*.*")))
        if filename:  # Check if a filename was actually selected
            # Extract both working directory and filename
            self.working_folder, self.filename = os.path.split(filename)

            # Handle potential empty working_dir if the user selects the root directory
            if self.working_folder:
                self.working_folder = os.path.abspath(self.working_folder)
                # Save the file using self.save() with extracted filename

                self.save()
            else:
                pass

    def save(self):
        """ create a dictionary of the thermal network"""
        serialized_nodes = self.thermal_network_tab.get_nodes()
        serialized_elm = self.thermal_network_tab.get_element()
        serialized_solution = self.thermal_network_tab.solution_Frame.serialize()
        serialized_functions = self.functions_dict

        # Serialize the object to a binary format

        data_to_save = {"Nodes": serialized_nodes,
                        "Elements": serialized_elm,
                        "Solution": serialized_solution,
                        "Functions": serialized_functions
                        }
        filepath = os.path.join(self.working_folder, self.filename)

        self.thermal_network_tab.bottomFrame.write_text('working folder: ' + self.working_folder + '\nfile name: ' +
                                                        self.filename + '\n')

        with open(filepath, 'wb') as f:
            pickle.dump(data_to_save, f)
        f.close()

    def close(self):
        check = messagebox.askyesnocancel(title="Close the network",
                                          message="Do you want to save the work before closing?")
        if check is True:
            self.save_network()
        elif check is False:
            self.thermal_network_tab.network_reset()
        elif check is None:
            pass

    def quit(self):
        check = messagebox.askyesnocancel(title="Quit the application",
                                          message="Do you want to save the work before closing?")
        if check is None:
            pass
        elif check is True:
            self.save_network()
        elif check is False:
            root.quit()

    def generate_input_file(self):
        self.thermal_network_tab.solution_Frame.update_analysis_info(1)
        if bool(self.thermal_network_tab.node_dict) and bool(self.thermal_network_tab.elm_dict):
            if self.working_folder:
                filename = os.path.splitext(self.filename)[0] + ".inp"
                filename = os.path.join(self.working_folder, filename)
                self.thermal_network_tab.bottomFrame.write_text(
                    'The input file is located here: {}\n'.format(filename))
                serialized_nodes = self.thermal_network_tab.get_nodes()
                serialized_elm = self.thermal_network_tab.get_element()
                TNSolver_input_file_gen(filename,
                                        self.thermal_network_tab.solution_Frame.get_analysis_setup(),
                                        serialized_nodes,
                                        serialized_elm,
                                        self.thermal_network_tab.solution_Frame.initialize_all,
                                        self.functions_dict)
            else:
                self.thermal_network_tab.bottomFrame.write_text(
                    'ERROR: The Working folder is not defined.\n')
        else:
            self.thermal_network_tab.bottomFrame.write_text(
                'ERROR: The model is not ready for an export: no nodes or element present.\n')
            pass

    def run_solver(self):
        if self.filename is None:
            self.save_network
            self.generate_input_file()

        self.thermal_network_tab.bottomFrame.write_text('Regenerating the solver input file...\n\n')
        self.generate_input_file()
        filename = os.path.splitext(self.filename)[0]
        base_file_name = os.path.join(self.working_folder, filename)
        T, Q, nd, el, spar = tn_solver(base_file_name, 2, self.thermal_network_tab.bottomFrame)
        self.thermal_network_tab.import_solution(T, Q, nd, el, spar)


# --------------------------------------------------------------------------------------------------------------------
#                                Root Frame
# --------------------------------------------------------------------------------------------------------------------

root = Tk()
root.title("Thermal Network Solver GUI")
root.iconbitmap('Pictures/icon_TNS.ico')
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
# root.geometry("%dx%d+0+0" % (w, h))
root.state("zoomed")
root.resizable(True, True)
root_size_grip = Sizegrip(root)
root_size_grip.pack(side="bottom", anchor="se")

MainApplication(root)
root.mainloop()
