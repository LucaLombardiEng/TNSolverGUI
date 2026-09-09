"""
    Main GUI for the TNSolver
    It is the GUI that permits the generation and manipulation of the TNSolver inputs.

    Luca Lombardi
    Rev 0: First Draft

    next steps:
        - add the background to the saved database
        - rebuild the background from the database

        TABS
        - create the user enclosure tab
        - create the user correlation tab
        - create the user init cond tab
        - create the converge tab

        Help/About
        - add license
        - add link to libraries used
"""
import pickle
import os
import numpy as np
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
from TNSolver_GUI.Material_TAB.material_manager_frame_MAIN import MaterialManager
from TNSolver_GUI.Radiation_Enclosure.Enclosure_TAB import RadiationEnclosureManager
from TNSolver_code.material_library import matlib


def win_about():
    revision = "1.0.0"
    mail = "luca.lombardi.ing@gmail.com"
    githubURL = "https://github.com/LucaLombardiEng/TNSolverGUI"
    TNSolver_url = "https://github.com/TNSolver/TNSolver"

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

    info_text = Label(win, text="TNSolver GUI {}\nCreated by Luca Lombardi\n\n"
                                "For info contact the author: {}\n\n"
                                "Source code available here: {}\n\n"
                                "The Original Matlab TNSolver code is available here: {}\n\n"
                                "Luca Lombardi 2025".format(revision, mail, githubURL, TNSolver_url),
                      wraplength=900, justify='left', bg="white", font=("Helvetica", 12))
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
        self.raw_materials = matlib()
        self.project_material_dict = self.convert_to_gui_dict(self.raw_materials)
        self.enclosure_dict = {}
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
        # 1. Instantiate Thermal Network Tab first (it creates bottomFrame / Terminal)
        self.thermal_network_tab = ThermalNetwork(self.tab_ctrl, self.functions_dict, self.project_material_dict)
        # Extract terminal logger callback reference
        logger_callback = self.thermal_network_tab.bottomFrame.write_text
        # 2. Pass logger_callback to other helper tabs
        self.user_function_tab = UserFunctionDefinition(self.tab_ctrl, self.functions_dict,
                                                        self.update_function_callback)
        self.user_material_tab = MaterialManager(self.tab_ctrl, self.project_material_dict,
                                                 self.update_material_callback, gUtility.path)
        self.user_enclosure_tab = RadiationEnclosureManager(parent=self.tab_ctrl,
                                                            main_network_ref=self.thermal_network_tab,
                                                            enclosure_dict=self.enclosure_dict,
                                                            # Shared dictionary reference
                                                            logger_cb=self.thermal_network_tab.bottomFrame.write_text)
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

    def update_material_callback(self):
        """
        This is the central method that user_function_tab calls to trigger an update.
        It then calls the specific update method on thermal_network_tab.
        """
        self.thermal_network_tab.update_material()

    @staticmethod
    def convert_to_gui_dict(materials_list):
        """Converts Material objects to the GUI-compatible dictionary format."""
        gui_dict = {}
        prop_map = [
            ('Thermal_Conductivity', 'ktype', 'kunits', 'kdata'),
            ('Mass_Density', 'rhotype', 'rhounits', 'rhodata'),
            ('Specific_Heat', 'cptype', 'cpunits', 'cpdata'),
            ('Dynamic_Viscosity', 'mutype', 'muunits', 'mudata'),
            ('Thermal_Expansion', 'betatype', 'betaunits', 'betadata'),
            ('Prandtl_Number', 'Prtype', 'Prunits', 'Prdata')
        ]

        for m in materials_list:
            mat_props = {}

            # Metadata
            state_labels = {1: "Solid", 2: "Liquid", 3: "Gas"}
            category = state_labels.get(m.state, "Other")
            mat_props['Category'] = {'type': 'scalar', 'value': state_labels.get(m.state, "Other"), 'unit': ''}

            # Logic: If it's a liquid or gas, it's definitely a FluidMaterial.
            # For "Other", you can set this manually or based on library flags.
            is_fluid = m.state in [2, 3] or category == "Other"  # Adjust logic as needed
            mat_props['Material_Type'] = {
                'type': 'scalar',
                'value': 'FluidMaterial' if is_fluid else 'SolidMaterial',
                'unit': ''
            }

            # Handle Standard/Tabular Properties (including Prandtl Number)
            for gui_name, type_attr, unit_attr, data_attr in prop_map:
                p_type_val = getattr(m, type_attr)
                p_units = getattr(m, unit_attr)
                p_data = getattr(m, data_attr)

                if p_data is not None:
                    if p_type_val == 1:  # CONST/Scalar
                        val = p_data[1] if isinstance(p_data, (np.ndarray, list)) and len(p_data) > 1 else p_data
                        mat_props[gui_name] = {
                            'type': 'scalar', 'value': str(val), 'unit': p_units[1] if p_units else ""
                        }
                    else:  # TABLE/SPLINE
                        q_vals = ",".join(map(str, p_data[:, 0]))
                        v_vals = ",".join(map(str, p_data[:, 1]))
                        mat_props[gui_name] = {
                            'type': 'table',
                            'qualifier_name': 'Temperature',
                            'qualifier_unit': p_units[0] if p_units else "K",
                            'qualifier_data': q_vals,
                            'param_name': gui_name,
                            'param_unit': p_units[1] if p_units else "",
                            'param_data': v_vals
                        }

            # Handle Gas Constant (Stored directly in m.R and m.Runits)
            if m.R is not None:
                mat_props['Gas_Constant'] = {
                    'type': 'scalar',
                    'value': str(m.R),
                    'unit': str(m.Runits) if m.Runits else "J/kg-K"
                }

            gui_dict[m.name] = mat_props

        return gui_dict

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

            # material dictionary reset and update
            self.project_material_dict.clear()
            # preserve the default materials
            self.project_material_dict.update(self.convert_to_gui_dict(self.raw_materials))
            self.user_material_tab.reset_database()

            # Enclosure dictionary reset
            self.enclosure_dict.clear()
            if hasattr(self.user_enclosure_tab, 'enclosures'):
                self.user_enclosure_tab.enclosures.clear()
                self.user_enclosure_tab.active_enclosure = None

            # updating the UI
            self.thermal_network_tab.bottomFrame.clear_text()
            self.thermal_network_tab.welcome_message()
            self.user_function_tab.data_frame.reset_all()
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
                # retrieve the Solver Setting
                if 'Solver Setting' in serialized_data:
                    self.thermal_network_tab.solution_Frame.setting_from_file(serialized_data["Solver Setting"])
                   
                    if serialized_data['Solver Setting']['analysis_type'] == 'Transient':
                        self.thermal_network_tab.slider_Frame.enable()
                        from_ = serialized_data['Solver Setting']['begin_time']
                        to_ = serialized_data['Solver Setting']['end_time']
                        steps = serialized_data['Solver Setting']['time_steps']
                        self.thermal_network_tab.slider_Frame.scale_configure([from_, to_, steps, to_])

                    else:
                        self.thermal_network_tab.slider_Frame.disable()
                   
                else:
                    self.thermal_network_tab.slider_Frame.disable()
                # retrieve the Functions definitions
                if 'Functions' in serialized_data:
                    if len(serialized_data['Functions']) > 1:
                        self.functions_dict.clear()  # clear the dictionary
                        self.functions_dict.update(serialized_data['Functions'])  # update the main function dictionary
                        # self.thermal_network_tab.update_functions()
                        self.thermal_network_tab.rightFrame.group_functions_by_unit()
                        self.user_function_tab.refresh_display()  # trigger the update of fn dictionary in fn tab
                else:
                    pass

                # retrieve the Material database
                if 'Materials' in serialized_data:
                    self.project_material_dict.clear()  # clear the dictionary
                    # update the main Material dictionary
                    self.project_material_dict.update(serialized_data['Materials'])
                    self.user_material_tab.reset_database()
                else:
                    pass

                # Retrieve Radiation Enclosures (Backward Compatible)
                self.enclosure_dict.clear()
                if 'Enclosures' in serialized_data:
                    self.enclosure_dict.update(serialized_data['Enclosures'])
                    # If RadiationEnclosureManager has internal state sync:
                    if hasattr(self, 'user_enclosure_tab'):
                        # Re-key loaded items into local UI structure
                        restored_enclosures = {}
                        for enc_id, enc_data in self.enclosure_dict.items():
                            surfaces = enc_data.get("surfaces", [])
                            areas = enc_data.get("areas", [])
                            eps = enc_data.get("emissivities", enc_data.get("eps", [0.85] * len(surfaces)))
                            vf_matrix = enc_data.get("view_factors", enc_data.get("F", []))

                            restored_enclosures[enc_id] = {
                                "surfaces": surfaces,
                                "areas": areas,
                                "eps": eps,
                                "F": np.array(vf_matrix, dtype=float) if len(vf_matrix) > 0 else np.empty((0, 0))
                            }

                        self.user_enclosure_tab.enclosures = restored_enclosures
                        self.user_enclosure_tab.sync_from_network()

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
        filename = filedialog.asksaveasfilename(initialdir=gUtility.working_folder_path,
                                                title="Select a File",
                                                defaultextension=".pkl",
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
        serialized_solver = self.thermal_network_tab.solution_Frame.serialize()
        serialized_functions = self.functions_dict
        serialized_materials = self.project_material_dict
        serialized_enclosures = self.enclosure_dict

        # Serialize the object to a binary format

        data_to_save = {"Nodes": serialized_nodes,
                        "Elements": serialized_elm,
                        "Solver Setting": serialized_solver,
                        "Functions": serialized_functions,
                        "Materials": serialized_materials,
                        "Enclosures": serialized_enclosures
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
                TNSolver_input_file_gen(
                    filename,
                    self.thermal_network_tab.solution_Frame.get_analysis_setup(),
                    serialized_nodes,
                    serialized_elm,
                    self.thermal_network_tab.solution_Frame.initialize_all,
                    self.functions_dict,
                    self.project_material_dict,
                    self.enclosure_dict
                )
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
